# frozen_string_literal: true

start_time = Time.now

require 'fileutils'
require 'optparse'
require 'pathname'
require_relative '../hpxml-measures/HPXMLtoOpenStudio/resources/meta_measure'
require_relative '../hpxml-measures/HPXMLtoOpenStudio/resources/version'

basedir = File.expand_path(File.dirname(__FILE__))

def rm_path(path)
  if Dir.exist?(path)
    FileUtils.rm_r(path)
  end
  while true
    break if not Dir.exist?(path)

    sleep(0.01)
  end
end

def get_rundir(output_dir, design)
  return File.join(output_dir, design.gsub(' ', ''))
end

def get_output_hpxml_path(resultsdir, rundir)
  return File.join(resultsdir, File.basename(rundir) + '.xml')
end

def run_design(basedir, rundir, resultsdir, json, hourly_output, debug, skip_simulation)
  measures_dir = File.join(basedir, '..')
  output_hpxml_path = get_output_hpxml_path(resultsdir, rundir)

  measures = {}

  # Add HEScore measure to workflow
  measure_subdir = 'rulesets/HEScoreRuleset'
  args = {}
  args['json_path'] = json
  args['hpxml_output_path'] = output_hpxml_path
  update_args_hash(measures, measure_subdir, args)

  if not skip_simulation
    # Add OS-HPXML translator measure to workflow
    measure_subdir = 'hpxml-measures/HPXMLtoOpenStudio'
    args = {}
    args['hpxml_path'] = output_hpxml_path
    args['output_dir'] = rundir
    args['debug'] = debug
    args['add_component_loads'] = false
    update_args_hash(measures, measure_subdir, args)

    # Add OS-HPXML reporting measure to workflow
    measure_subdir = 'hpxml-measures/ReportSimulationOutput'
    args = {}
    args['timeseries_frequency'] = 'monthly'
    args['include_timeseries_end_use_consumptions'] = true
    args['include_timeseries_hot_water_uses'] = true
    args['timeseries_output_file_name'] = 'results_monthly.csv'
    update_args_hash(measures, measure_subdir, args)

    # Add HEScore reporting measure to workflow
    measure_subdir = 'rulesets/ReportHEScoreOutput'
    args = {}
    args['json_path'] = json
    args['hpxml_path'] = output_hpxml_path
    args['json_output_path'] = File.join(resultsdir, 'results.json')
    update_args_hash(measures, measure_subdir, args)

    if hourly_output
      # Add reporting measure to workflow
      measure_subdir = 'hpxml-measures/ReportSimulationOutput'
      args = {}
      args['timeseries_frequency'] = 'hourly'
      args['include_timeseries_end_use_consumptions'] = true
      args['include_timeseries_hot_water_uses'] = true
      args['timeseries_output_file_name'] = 'results_hourly.csv'
      update_args_hash(measures, measure_subdir, args)
    end
  end

  results = run_hpxml_workflow(rundir, measures, measures_dir,
                               debug: debug, run_measures_only: skip_simulation)

  return results[:success]
end

def download_epws
  require_relative '../hpxml-measures/HPXMLtoOpenStudio/resources/util'

  weather_dir = File.join(File.dirname(__FILE__), '..', 'weather')

  num_epws_expected = 1011
  num_epws_actual = Dir[File.join(weather_dir, '*.epw')].count
  num_cache_expcted = num_epws_expected
  num_cache_actual = Dir[File.join(weather_dir, '*-cache.csv')].count
  if (num_epws_actual == num_epws_expected) && (num_cache_actual == num_cache_expcted)
    puts 'Weather directory is already up-to-date.'
    puts "#{num_epws_actual} weather files are available in the weather directory."
    puts 'Completed.'
    exit!
  end

  require 'tempfile'
  tmpfile = Tempfile.new('epw')

  UrlResolver.fetch('https://data.nrel.gov/system/files/128/tmy3s-cache-csv.zip', tmpfile)

  puts 'Extracting weather files...'
  require 'zip'
  Zip.on_exists_proc = true
  Zip::File.open(tmpfile.path.to_s) do |zip_file|
    zip_file.each do |f|
      zip_file.extract(f, File.join(weather_dir, f.name))
    end
  end

  num_epws_actual = Dir[File.join(weather_dir, '*.epw')].count
  puts "#{num_epws_actual} weather files are available in the weather directory."
  puts 'Completed.'
  exit!
end

options = {}
OptionParser.new do |opts|
  opts.banner = "Usage: #{File.basename(__FILE__)} -j building.json\n e.g., #{File.basename(__FILE__)} -j regression_files/Base.json\n"

  opts.on('-j', '--json <FILE>', 'JSON file') do |t|
    options[:json] = t
  end

  opts.on('-o', '--output-dir <DIR>', 'Output directory') do |t|
    options[:output_dir] = t
  end

  options[:hourly_output] = false
  opts.on('--hourly', 'Request hourly output CSV') do |_t|
    options[:hourly_output] = true
  end

  opts.on('-w', '--download-weather', 'Downloads all weather files') do |t|
    options[:epws] = t
  end

  options[:skip_simulation] = false
  opts.on('--skip-simulation', 'Skip the EnergyPlus simulation') do |_t|
    options[:skip_simulation] = true
  end

  options[:debug] = false
  opts.on('-d', '--debug') do |_t|
    options[:debug] = true
  end

  opts.on_tail('-h', '--help', 'Display help') do
    puts opts
    exit!
  end
end.parse!

if options[:epws]
  download_epws
end

if not options[:json]
  fail "JSON argument is required. Call #{File.basename(__FILE__)} -h for usage."
end

unless (Pathname.new options[:json]).absolute?
  options[:json] = File.expand_path(options[:json])
end
unless File.exist?(options[:json]) && options[:json].downcase.end_with?('.json')
  fail "'#{options[:json]}' does not exist or is not an .json file."
end

# Check for correct versions of OS
Version.check_openstudio_version()

if options[:output_dir].nil?
  options[:output_dir] = basedir # default
end
options[:output_dir] = File.expand_path(options[:output_dir])

unless Dir.exist?(options[:output_dir])
  FileUtils.mkdir_p(options[:output_dir])
end

# Create results dir
resultsdir = File.join(options[:output_dir], 'results')
rm_path(resultsdir)
Dir.mkdir(resultsdir)

# Run design
puts "JSON: #{options[:json]}"
design = 'HEScoreDesign'
rundir = get_rundir(options[:output_dir], design)

success = run_design(basedir, rundir, resultsdir, options[:json], options[:hourly_output],
                     options[:debug], options[:skip_simulation])

if not success
  exit! 1
end

puts "Completed in #{(Time.now - start_time).round(1)} seconds."
