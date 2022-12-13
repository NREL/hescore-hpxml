# frozen_string_literal: true

def create_jsons()
  this_dir = File.dirname(__FILE__)
  json_inputs_path = File.join(this_dir, 'workflow/json_inputs.tsv')
  json_inputs = CSV.parse(File.read(json_inputs_path), headers: true, col_sep: "\t")

  json_inputs.each_with_index do |row, i|
    json_filename = json_inputs[i]['file_name']
    json_filepath = File.join(this_dir, "workflow/#{json_inputs[i]['file_type']}/#{json_inputs[i]['file_name']}")

    puts "[#{i + 1}/#{json_inputs.length}] Generating #{json_filename}..."

    json_data = set_json_property_values(json_inputs[i])

    begin
      if json_filepath.include? '328769.json'
        raise "Temporary CI test"
      end
      File.open(json_filepath, 'w') do |f|
        f.write(JSON.pretty_generate(json_data))
      end
    rescue Exception => e
      puts "\n#{e}\n#{e.backtrace.join('\n')}"
      puts "\nError: Did not successfully generate #{json_file}."
      exit!
    end
  end
end

def set_json_property_values(json_input)
  data = Hash.new { |h, k| h[k] = h.dup.clear }
  data['building_address']['address'] = json_input['address'] unless json_input['address'].nil?
  data['building_address']['city'] = json_input['city'] unless json_input['city'].nil?
  data['building_address']['state'] = json_input['state'] unless json_input['state'].nil?
  data['building_address']['zip_code'] = '%05d' % json_input['zip_code'] unless json_input['zip_code'].nil?
  data['building_address']['assessment_type'] = json_input['assessment_type'] unless json_input['assessment_type'].nil?
  data['building_address']['external_building_id'] = json_input['external_building_id'] unless json_input['external_building_id'].nil?

  data['building']['about']['assessment_date'] = json_input['assessment_date'] unless json_input['assessment_date'].nil?
  data['building']['about']['shape'] = json_input['shape'] unless json_input['shape'].nil?
  data['building']['about']['town_house_walls'] = json_input['town_house_walls'] unless json_input['town_house_walls'].nil?
  data['building']['about']['year_built'] = Integer(json_input['year_built']) unless json_input['year_built'].nil?
  data['building']['about']['number_bedrooms'] = Integer(json_input['number_bedrooms']) unless json_input['number_bedrooms'].nil?
  data['building']['about']['num_floor_above_grade'] = Integer(json_input['num_floor_above_grade']) unless json_input['num_floor_above_grade'].nil?
  data['building']['about']['floor_to_ceiling_height'] = Integer(json_input['floor_to_ceiling_height']) unless json_input['floor_to_ceiling_height'].nil?
  data['building']['about']['conditioned_floor_area'] = Float(json_input['conditioned_floor_area']) unless json_input['conditioned_floor_area'].nil?
  data['building']['about']['orientation'] = json_input['orientation'] unless json_input['orientation'].nil?
  data['building']['about']['blower_door_test'] = (json_input['blower_door_test'] == 'TRUE' ? true : false) unless json_input['blower_door_test'].nil?
  data['building']['about']['air_sealing_present'] = (json_input['air_sealing_present'] == 'TRUE' ? true : false) unless json_input['air_sealing_present'].nil?
  data['building']['about']['envelope_leakage'] = Integer(json_input['envelope_leakage']) unless json_input['envelope_leakage'].nil?

  zone_roof = []
  2.times do |i|
    id = (i + 1).to_s
    next if json_input["roof_name_#{id}"].nil?

    zone_roof_hash = Hash.new { |h, k| h[k] = h.dup.clear }
    zone_roof_hash['roof_name'] = json_input["roof_name_#{id}"] unless json_input["roof_name_#{id}"].nil?
    zone_roof_hash['roof_area'] = Float(json_input["roof_area_#{id}"]) unless json_input["roof_area_#{id}"].nil?
    zone_roof_hash['ceiling_area'] = Float(json_input["ceiling_area_#{id}"]) unless json_input["ceiling_area_#{id}"].nil?
    zone_roof_hash['roof_assembly_code'] = json_input["roof_assembly_code_#{id}"] unless json_input["roof_assembly_code_#{id}"].nil?
    zone_roof_hash['roof_color'] = json_input["roof_color_#{id}"] unless json_input["roof_color_#{id}"].nil?
    zone_roof_hash['roof_absorptance'] = Float(json_input["roof_absorptance_#{id}"]) unless json_input["roof_absorptance_#{id}"].nil?
    zone_roof_hash['roof_type'] = json_input["roof_type_#{id}"] unless json_input["roof_type_#{id}"].nil?
    zone_roof_hash['ceiling_assembly_code'] = json_input["ceiling_assembly_code_#{id}"] unless json_input["ceiling_assembly_code_#{id}"].nil?
    zone_roof_hash['knee_wall']['assembly_code'] = json_input["knee_wall_assembly_code_#{id}"] unless json_input["knee_wall_assembly_code_#{id}"].nil?
    zone_roof_hash['knee_wall']['area'] = Float(json_input["knee_wall_area_#{id}"]) unless json_input["knee_wall_area_#{id}"].nil?
    zone_roof_hash['zone_skylight']['skylight_area'] = Float(json_input["skylight_area_#{id}"]) unless json_input["skylight_area_#{id}"].nil?
    zone_roof_hash['zone_skylight']['skylight_method'] = json_input["skylight_method_#{id}"] unless json_input["skylight_method_#{id}"].nil?
    zone_roof_hash['zone_skylight']['skylight_code'] = json_input["skylight_code_#{id}"] unless json_input["skylight_code_#{id}"].nil?
    zone_roof_hash['zone_skylight']['skylight_u_value'] = Float(json_input["skylight_u_value_#{id}"]) unless json_input["skylight_u_value_#{id}"].nil?
    zone_roof_hash['zone_skylight']['skylight_shgc'] = Float(json_input["skylight_shgc_#{id}"]) unless json_input["skylight_shgc_#{id}"].nil?
    zone_roof_hash['zone_skylight']['solar_screen'] = (json_input["skylight_solar_screen_#{id}"] == 'TRUE' ? true : false) unless json_input["skylight_solar_screen_#{id}"].nil?
    zone_roof_hash['zone_skylight']['storm_type'] = json_input["skylight_storm_type_#{id}"] unless json_input["skylight_storm_type_#{id}"].nil?

    zone_roof[i] = zone_roof_hash
  end
  data['building']['zone']['zone_roof'] = zone_roof

  zone_floor = []
  2.times do |i|
    id = (i + 1).to_s
    next if json_input["floor_name_#{id}"].nil?

    zone_floor_hash = Hash.new { |h, k| h[k] = h.dup.clear }
    zone_floor_hash['floor_name'] = json_input["floor_name_#{id}"] unless json_input["floor_name_#{id}"].nil?
    zone_floor_hash['floor_area'] = Float(json_input["floor_area_#{id}"]) unless json_input["floor_area_#{id}"].nil?
    zone_floor_hash['foundation_type'] = json_input["foundation_type_#{id}"] unless json_input["foundation_type_#{id}"].nil?
    zone_floor_hash['foundation_insulation_level'] = Integer(json_input["foundation_insulation_level_#{id}"]) unless json_input["foundation_insulation_level_#{id}"].nil?
    zone_floor_hash['floor_assembly_code'] = json_input["floor_assembly_code_#{id}"] unless json_input["floor_assembly_code_#{id}"].nil?
    zone_floor[i] = zone_floor_hash
  end
  data['building']['zone']['zone_floor'] = zone_floor

  data['building']['zone']['wall_construction_same'] = (json_input['wall_construction_same'] == 'TRUE' ? true : false) unless json_input['wall_construction_same'].nil?
  data['building']['zone']['window_construction_same'] = (json_input['window_construction_same'] == 'TRUE' ? true : false) unless json_input['window_construction_same'].nil?

  zone_wall = []
  4.times do |i|
    id = (i + 1).to_s
    next if json_input["wall#{id}_side"].nil?

    zone_wall_hash = Hash.new { |h, k| h[k] = h.dup.clear }
    zone_wall_hash['side'] = json_input["wall#{id}_side"] unless json_input["wall#{id}_side"].nil?
    zone_wall_hash['wall_assembly_code'] = json_input["wall#{id}_assembly_code"] unless json_input["wall#{id}_assembly_code"].nil?
    zone_wall_hash['zone_window']['window_area'] = Float(json_input["window#{id}_area"]) unless json_input["window#{id}_area"].nil?
    zone_wall_hash['zone_window']['window_method'] = json_input["window#{id}_method"] unless json_input["window#{id}_method"].nil?
    zone_wall_hash['zone_window']['window_code'] = json_input["window#{id}_code"] unless json_input["window#{id}_code"].nil?
    zone_wall_hash['zone_window']['window_u_value'] = Float(json_input["window#{id}_u_value"]) unless json_input["window#{id}_u_value"].nil?
    zone_wall_hash['zone_window']['window_shgc'] = Float(json_input["window#{id}_shgc"]) unless json_input["window#{id}_shgc"].nil?
    zone_wall_hash['zone_window']['solar_screen'] = (json_input["window#{id}_solar_screen"] == 'TRUE' ? true : false) unless json_input["window#{id}_solar_screen"].nil?
    zone_wall_hash['zone_window']['storm_type'] = json_input["window#{id}_storm_type"] unless json_input["window#{id}_storm_type"].nil?
    zone_wall[i] = zone_wall_hash
  end
  data['building']['zone']['zone_wall'] = zone_wall

  hvac = []
  2.times do |i|
    id = (i + 1).to_s
    next if json_input["hvac_name_#{id}"].nil?

    hvac_hash = Hash.new { |h, k| h[k] = h.dup.clear }
    hvac_hash['hvac_name'] = json_input["hvac_name_#{id}"] unless json_input["hvac_name_#{id}"].nil?
    hvac_hash['hvac_fraction'] = Float(json_input["hvac_fraction_#{id}"]) unless json_input["hvac_fraction_#{id}"].nil?
    hvac_hash['heating']['fuel_primary'] = json_input["heating_fuel_primary_#{id}"] unless json_input["heating_fuel_primary_#{id}"].nil?
    hvac_hash['heating']['type'] = json_input["heating_type_#{id}"] unless json_input["heating_type_#{id}"].nil?
    hvac_hash['heating']['efficiency_method'] = json_input["heating_efficiency_method_#{id}"] unless json_input["heating_efficiency_method_#{id}"].nil?
    hvac_hash['heating']['efficiency'] = Float(json_input["heating_efficiency_#{id}"]) unless json_input["heating_efficiency_#{id}"].nil?
    hvac_hash['heating']['efficiency_level'] = json_input["heating_efficiency_level_#{id}"] unless json_input["heating_efficiency_level_#{id}"].nil?
    hvac_hash['heating']['year'] = Integer(json_input["heating_year_#{id}"]) unless json_input["heating_year_#{id}"].nil?
    hvac_hash['cooling']['type'] = json_input["cooling_type_#{id}"] unless json_input["cooling_type_#{id}"].nil?
    hvac_hash['cooling']['efficiency_method'] = json_input["cooling_efficiency_method_#{id}"] unless json_input["cooling_efficiency_method_#{id}"].nil?
    hvac_hash['cooling']['efficiency'] = Float(json_input["cooling_efficiency_#{id}"]) unless json_input["cooling_efficiency_#{id}"].nil?
    hvac_hash['cooling']['efficiency_level'] = json_input["cooling_efficiency_level_#{id}"] unless json_input["cooling_efficiency_level_#{id}"].nil?
    hvac_hash['cooling']['year'] = Integer(json_input["cooling_year_#{id}"]) unless json_input["cooling_year_#{id}"].nil?
    hvac_hash['hvac_distribution']['leakage_method'] = json_input["duct_leakage_method_#{id}"] unless json_input["duct_leakage_method_#{id}"].nil?
    hvac_hash['hvac_distribution']['leakage_to_outside'] = Float(json_input["duct_leakage_to_outside_#{id}"]) unless json_input["duct_leakage_to_outside_#{id}"].nil?
    hvac_hash['hvac_distribution']['sealed'] = (json_input["duct_sealed_#{id}"] == 'TRUE' ? true : false) unless json_input["duct_sealed_#{id}"].nil?

    duct = []
    3.times do |j|
      duct_id = (j + 1).to_s
      next if json_input["duct#{duct_id}_name_#{id}"].nil?

      duct_hash = Hash.new { |h, k| h[k] = h.dup.clear }
      duct_hash['name'] = json_input["duct#{duct_id}_name_#{id}"] unless json_input["duct#{duct_id}_name_#{id}"].nil?
      duct_hash['location'] = json_input["duct#{duct_id}_location_#{id}"] unless json_input["duct#{duct_id}_location_#{id}"].nil?
      duct_hash['fraction'] = Float(json_input["duct#{duct_id}_fraction_#{id}"]) unless json_input["duct#{duct_id}_fraction_#{id}"].nil?
      duct_hash['insulated'] = (json_input["duct#{duct_id}_insulated_#{id}"] == 'TRUE' ? true : false) unless json_input["duct#{duct_id}_insulated_#{id}"].nil?
      duct[j] = duct_hash
    end
    hvac_hash['hvac_distribution']['duct'] = duct unless duct.empty?

    hvac[i] = hvac_hash
  end
  data['building']['systems']['hvac'] = hvac

  data['building']['systems']['domestic_hot_water']['category'] = json_input['hw_category'] unless json_input['hw_category'].nil?
  data['building']['systems']['domestic_hot_water']['type'] = json_input['hw_type'] unless json_input['hw_type'].nil?
  data['building']['systems']['domestic_hot_water']['fuel_primary'] = json_input['hw_fuel_primary'] unless json_input['hw_fuel_primary'].nil?
  data['building']['systems']['domestic_hot_water']['efficiency_method'] = json_input['hw_efficiency_method'] unless json_input['hw_efficiency_method'].nil?
  data['building']['systems']['domestic_hot_water']['efficiency_level'] = json_input['hw_efficiency_level'] unless json_input['hw_efficiency_level'].nil?
  data['building']['systems']['domestic_hot_water']['energy_factor'] = Float(json_input['hw_energy_factor']) unless json_input['hw_energy_factor'].nil?
  data['building']['systems']['domestic_hot_water']['year'] = Integer(json_input['hw_year']) unless json_input['hw_year'].nil?

  data['building']['systems']['generation']['solar_electric']['capacity_known'] = (json_input['pv_capacity_known'] == 'TRUE' ? true : false) unless json_input['pv_capacity_known'].nil?
  data['building']['systems']['generation']['solar_electric']['system_capacity'] = Float(json_input['pv_system_capacity']) unless json_input['pv_system_capacity'].nil?
  data['building']['systems']['generation']['solar_electric']['year'] = Integer(json_input['pv_year']) unless json_input['pv_year'].nil?
  data['building']['systems']['generation']['solar_electric']['array_azimuth'] = json_input['pv_array_azimuth'] unless json_input['pv_array_azimuth'].nil?
  data['building']['systems']['generation']['solar_electric']['array_tilt'] = json_input['pv_array_tilt'] unless json_input['pv_array_tilt'].nil?
  data['building']['systems']['generation']['solar_electric']['num_panels'] = Integer(json_input['pv_num_panels']) unless json_input['pv_num_panels'].nil?

  return data
end

command_list = [:update_measures, :update_jsons]

def display_usage(command_list)
  puts "Usage: openstudio #{File.basename(__FILE__)} [COMMAND]\nCommands:\n  " + command_list.join("\n  ")
end

if ARGV.size == 0
  puts 'ERROR: Missing command.'
  display_usage(command_list)
  exit!
elsif ARGV.size > 1
  puts 'ERROR: Too many commands.'
  display_usage(command_list)
  exit!
elsif not command_list.include? ARGV[0].to_sym
  puts "ERROR: Invalid command '#{ARGV[0]}'."
  display_usage(command_list)
  exit!
end

if ARGV[0].to_sym == :update_measures
  # Prevent NREL error regarding U: drive when not VPNed in
  ENV['HOME'] = 'C:' if !ENV['HOME'].nil? && ENV['HOME'].start_with?('U:')
  ENV['HOMEDRIVE'] = 'C:\\' if !ENV['HOMEDRIVE'].nil? && ENV['HOMEDRIVE'].start_with?('U:')

  # Apply rubocop
  cops = ['Layout',
          'Lint/DeprecatedClassMethods',
          # 'Lint/RedundantStringCoercion', # Enable when rubocop is upgraded
          'Style/AndOr',
          'Style/FrozenStringLiteralComment',
          'Style/HashSyntax',
          'Style/Next',
          'Style/NilComparison',
          'Style/RedundantParentheses',
          'Style/RedundantSelf',
          'Style/ReturnNil',
          'Style/SelfAssignment',
          'Style/StringLiterals',
          'Style/StringLiteralsInInterpolation']
  commands = ["\"require 'rubocop/rake_task'\"",
              "\"RuboCop::RakeTask.new(:rubocop) do |t| t.options = ['--auto-correct', '--format', 'simple', '--only', '#{cops.join(',')}'] end\"",
              '"Rake.application[:rubocop].invoke"']
  command = "#{OpenStudio.getOpenStudioCLI} -e #{commands.join(' -e ')}"
  puts 'Applying rubocop auto-correct to measures...'
  system(command)

  # Update measures XMLs
  require 'oga'
  require_relative 'hpxml-measures/HPXMLtoOpenStudio/resources/xmlhelper'
  puts 'Updating measure.xmls...'
  Dir['**/measure.xml'].each do |measure_xml|
    for n_attempt in 1..5 # For some reason CLI randomly generates errors, so try multiple times; FIXME: Fix CLI so this doesn't happen
      measure_dir = File.dirname(measure_xml)
      command = "#{OpenStudio.getOpenStudioCLI} measure -u '#{measure_dir}'"
      system(command, [:out, :err] => File::NULL)

      # Check for error
      xml_doc = XMLHelper.parse_file(measure_xml)
      err_val = XMLHelper.get_value(xml_doc, '/measure/error', :string)
      if err_val.nil?
        err_val = XMLHelper.get_value(xml_doc, '/error', :string)
      end
      if err_val.nil?
        break # Successfully updated
      else
        if n_attempt == 5
          fail "#{measure_xml}: #{err_val}" # Error generated all 5 times, fail
        else
          # Remove error from measure XML, try again
          new_lines = File.readlines(measure_xml).select { |l| !l.include?('<error>') }
          File.open(measure_xml, 'w') do |file|
            file.puts new_lines
          end
        end
      end
    end
  end

  puts 'Done.'
end

if ARGV[0].to_sym == :update_jsons
  # Prevent NREL error regarding U: drive when not VPNed in
  ENV['HOME'] = 'C:' if !ENV['HOME'].nil? && ENV['HOME'].start_with?('U:')
  ENV['HOMEDRIVE'] = 'C:\\' if !ENV['HOMEDRIVE'].nil? && ENV['HOMEDRIVE'].start_with?('U:')

  require 'json'
  require 'csv'
  # Create sample/test JSONs
  create_jsons()
end
