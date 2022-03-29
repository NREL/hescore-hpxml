# frozen_string_literal: true

# see the URL below for information on how to write OpenStudio measures
# http://nrel.github.io/OpenStudio-user-documentation/reference/measure_writing_guide/

require 'csv'
require_relative '../../workflow/hescore_lib'

# start the measure
class ReportHEScoreOutput < OpenStudio::Measure::ReportingMeasure
  # human readable name
  def name
    # Measure name should be the title case of the class name.
    return 'Report HEScore Output'
  end

  # human readable description
  def description
    return 'Reports simulation-based outputs for HEScore runs.'
  end

  # human readable description of modeling approach
  def modeler_description
    return ''
  end

  # define the arguments that the user will input
  def arguments(model)
    args = OpenStudio::Measure::OSArgumentVector.new

    arg = OpenStudio::Measure::OSArgument::makeStringArgument('results_dir', true)
    arg.setDisplayName('Results Directory')
    arg.setDescription('Path to the directory where any output files (e.g., results.json) will be written.')
    args << arg

    return args
  end

  # define what happens when the measure is run
  def run(runner, user_arguments)
    super(runner, user_arguments)

    model = runner.lastOpenStudioModel
    if model.empty?
      runner.registerError('Cannot find OpenStudio model.')
      return false
    end
    model = model.get
    @model = model

    # use the built-in error checking
    if !runner.validateUserArguments(arguments(model), user_arguments)
      return false
    end

    resultsdir = runner.getStringArgumentValue('results_dir', user_arguments)

    sqlFile = runner.lastEnergyPlusSqlFile
    if sqlFile.empty?
      runner.registerError('Cannot find EnergyPlus sql file.')
      return false
    end

    rundir = File.dirname(sqlFile.get.path.to_s)

    # Gather monthly outputs for results JSON
    monthly_csv_path = File.join(rundir, 'results_monthly.csv')
    return false unless File.exist? monthly_csv_path

    units_map = get_units_map()
    output_map = get_output_map()
    outputs = {}
    output_map.each do |ep_output, hes_output|
      outputs[hes_output] = []
    end
    row_index = {}
    units = nil
    CSV.foreach(monthly_csv_path).with_index do |row, row_num|
      if row_num == 0 # Header
        output_map.each do |ep_output, hes_output|
          row_index[ep_output] = row.index(ep_output)
        end
      elsif row_num == 1 # Units
        units = row
      else # Data
        # Init for month
        outputs.keys.each do |k|
          outputs[k] << 0.0
        end
        # Add values
        output_map.each do |ep_output, hes_output|
          col = row_index[ep_output]
          next if col.nil?

          outputs[hes_output][-1] += UnitConversions.convert(Float(row[col]), units[col], units_map[hes_output[1]].gsub('gallons', 'gal')).abs
        end
        # Make sure there aren't any end uses with positive values that aren't mapped to HES
        row.each_with_index do |val, col|
          next if col.nil?
          next if col == 0 # Skip time column
          next if row_index.values.include? col

          fail "Missed value (#{val}) in row=#{row_num}, col=#{col}." if Float(val) > 0
        end
      end
    end

    # Write results to JSON
    data = { 'end_use' => [] }
    outputs.each do |hes_key, values|
      hes_end_use, hes_resource_type = hes_key
      to_units = units_map[hes_resource_type]
      annual_value = values.inject(0, :+)
      next if annual_value <= 0.01

      values.each_with_index do |value, idx|
        end_use = { 'quantity' => value,
                    'period_type' => 'month',
                    'period_number' => (idx + 1).to_s,
                    'end_use' => hes_end_use,
                    'resource_type' => hes_resource_type,
                    'units' => to_units }
        data['end_use'] << end_use
      end
    end

    require 'json'
    File.open(File.join(resultsdir, 'results.json'), 'w') do |f|
      f.write(JSON.pretty_generate(data))
    end

    return true
  end
end

# register the measure to be used by the application
ReportHEScoreOutput.new.registerWithApplication
