# frozen_string_literal: true

# see the URL below for information on how to write OpenStudio measures
# http://nrel.github.io/OpenStudio-user-documentation/reference/measure_writing_guide/

require 'csv'
require 'json'
require_relative '../../workflow/hescore_lib'

# start the measure
class ReportHEScoreOutput < OpenStudio::Measure::ReportingMeasure
  ELECTRIC_SITE_TO_SOURCE = 2.76
  NATURAL_GAS_SITE_TO_SOURCE = 1.05
  FUEL_OIL_SITE_TO_SOURCE = 1.01
  LPG_SITE_TO_SOURCE = 1.01
  KEROSENE_SITE_TO_SOURCE = 1.01
  WOOD_SITE_TO_SOURCE = 1.0

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

    arg = OpenStudio::Measure::OSArgument.makeStringArgument('json_path', true)
    arg.setDisplayName('JSON File Path')
    arg.setDescription('Absolute (or relative) path of the JSON file.')
    args << arg

    arg = OpenStudio::Measure::OSArgument.makeStringArgument('hpxml_path', true)
    arg.setDisplayName('HPXML File Path')
    arg.setDescription('Absolute/relative path of the HPXML file.')
    args << arg

    arg = OpenStudio::Measure::OSArgument::makeStringArgument('json_output_path', false)
    arg.setDisplayName('JSON Output File Path')
    arg.setDescription('Absolute (or relative) path of the output HPXML file.')
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

    # use the built-in error checking
    if !runner.validateUserArguments(arguments(model), user_arguments)
      return false
    end

    json_path = runner.getStringArgumentValue('json_path', user_arguments)
    hpxml_path = runner.getStringArgumentValue('hpxml_path', user_arguments)
    json_output_path = runner.getOptionalStringArgumentValue('json_output_path', user_arguments)
    if json_output_path.is_initialized
      json_output_path = json_output_path.get
    else
      json_output_path = nil
    end

    sqlFile = runner.lastEnergyPlusSqlFile
    if sqlFile.empty?
      runner.registerError('Cannot find EnergyPlus sql file.')
      return false
    end

    rundir = File.dirname(sqlFile.get.path.to_s)

    json_data = { 'end_use' => [] }

    # Gather monthly outputs for results JSON
    monthly_csv_path = File.join(rundir, 'results_monthly.csv')
    if not File.exist? monthly_csv_path
      runner.registerError('Cannot find results_monthly.csv file.')
      return false
    end

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

    # Create results for JSON
    outputs.each do |hes_key, values|
      hes_end_use, hes_resource_type = hes_key
      to_units = units_map[hes_resource_type]
      annual_value = values.sum
      next if annual_value <= 0.01

      values.each_with_index do |value, idx|
        end_use = { 'quantity' => value,
                    'period_type' => 'month',
                    'period_number' => (idx + 1).to_s,
                    'end_use' => hes_end_use,
                    'resource_type' => hes_resource_type,
                    'units' => to_units }
        json_data['end_use'] << end_use
      end
    end

    # Calculate the source energy
    site_to_source_map = { 'electric' => ELECTRIC_SITE_TO_SOURCE,
                           'natural_gas' => NATURAL_GAS_SITE_TO_SOURCE,
                           'lpg' => LPG_SITE_TO_SOURCE,
                           'fuel_oil' => FUEL_OIL_SITE_TO_SOURCE,
                           'cord_wood' => WOOD_SITE_TO_SOURCE,
                           'pellet_wood' => WOOD_SITE_TO_SOURCE }
    total_source_energy = 0.0
    asset_source_energy = 0.0
    outputs.each do |hes_key, values|
      hes_end_use, hes_resource_type = hes_key
      if hes_end_use == 'generation' # PV generation gets a _site_ energy credit
        site_to_source_factor = -1.0
      else
        site_to_source_factor = site_to_source_map[hes_resource_type]
      end
      next if site_to_source_factor.nil?

      units = units_map[hes_resource_type]
      total_source_energy += UnitConversions.convert(values.sum, units, 'MBtu') * site_to_source_factor

      next unless ['heating', 'cooling', 'hot_water', 'generation'].include? hes_end_use

      asset_source_energy += UnitConversions.convert(values.sum, units, 'MBtu') * site_to_source_factor
    end
    { 'total_source_energy' => total_source_energy,
      'asset_source_energy' => asset_source_energy }.each do |resource_type, quantity|
      quantity = quantity.round(2)
      end_use = { 'quantity' => quantity,
                  'period_type' => 'year',
                  'resource_type' => resource_type,
                  'units' => 'MBtu' }
      json_data['end_use'] << end_use
      runner.registerValue(resource_type, quantity)
      runner.registerInfo("Registering #{quantity} for #{resource_type}.")
    end

    # Calculate the score
    hpxml = HPXML.new(hpxml_path: hpxml_path)
    weather_station = hpxml.climate_and_risk_zones.weather_station_wmo.to_i
    runner.registerValue('weather_station', weather_station)
    runner.registerInfo("Registering #{weather_station} for weather_station.")
    score = calc_score(runner, weather_station, asset_source_energy)
    if score.nil?
      runner.registerError('Cannot calculate score.')
      return false
    end

    resource_type = 'score'
    end_use = { 'quantity' => score,
                'resource_type' => resource_type }
    json_data['end_use'] << end_use
    runner.registerValue(resource_type, score)
    runner.registerInfo("Registering #{score} for #{resource_type}.")

    # Write results to JSON
    if not json_output_path.nil?
      File.open(json_output_path, 'w') do |f|
        f.write(JSON.pretty_generate(json_data))
      end
    end

    # Register the HEScore inputs as outputs
    hes_inputs = JSON.parse(File.read(json_path))
    hes_inputs_flat = flatten(hes_inputs)
    hes_inputs_flat.each do |k, v|
      runner.registerValue(k, v)
      runner.registerInfo("Registering #{v} for #{k}.")
    end

    return true
  end

  def calc_score(runner, weather_station, asset_source_energy)
    bins_file = File.join(File.dirname(__FILE__), 'resources', 'bins.csv')
    score = nil
    CSV.foreach(bins_file, headers: true) do |row|
      if row['weather_station_id'].to_i == weather_station
        (2..10).each do |i|
          if asset_source_energy.round > row[i.to_s].to_i
            return i - 1
          end
        end
        return 10
      end
    end
    runner.registerError("Unable to find weather station #{weather_station} in bins.")
  end

  def flatten(obj, prefix = [])
    new_obj = {}
    if obj.is_a?(Hash)
      obj.each do |k, v|
        new_prefix = prefix + [k]
        flatten(v, new_prefix).each do |k2, v2|
          new_obj[k2] = v2
        end
      end
    elsif obj.is_a?(Array)
      obj.each_with_index do |v, i|
        new_prefix = prefix + [i.to_s]
        flatten(v, new_prefix).each do |k2, v2|
          new_obj[k2] = v2
        end
      end
    else
      new_obj[prefix.join('-')] = obj
    end
    return new_obj
  end
end

# register the measure to be used by the application
ReportHEScoreOutput.new.registerWithApplication
