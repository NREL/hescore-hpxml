# frozen_string_literal: true

# see the URL below for information on how to write OpenStudio measures
# http://nrel.github.io/OpenStudio-user-documentation/reference/measure_writing_guide/

require 'csv'
require 'json'
require_relative '../../workflow/hescore_lib'

# start the measure
class ReportHEScoreOutput < OpenStudio::Measure::ReportingMeasure
  # kBtu/kBtu
  ELECTRIC_SITE_TO_SOURCE = 2.58
  NATURAL_GAS_SITE_TO_SOURCE = 1.05
  FUEL_OIL_SITE_TO_SOURCE = 1.01
  LPG_SITE_TO_SOURCE = 1.01
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

    hpxml = HPXML.new(hpxml_path: hpxml_path, collapse_enclosure: false)

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

    # Calculate monthly end use outputs (site energy)
    units_map = get_units_map()
    outputs = retrieve_hescore_outputs(monthly_csv_path, units_map)
    outputs.each do |hes_key, values|
      hes_end_use, hes_resource_type = hes_key
      to_units = units_map[hes_resource_type]
      annual_value = values.sum
      next if annual_value <= 0.01

      values.each_with_index do |value, idx|
        json_data['end_use'] << { 'quantity' => value,
                                  'period_type' => 'month',
                                  'period_number' => (idx + 1).to_s,
                                  'end_use' => hes_end_use,
                                  'resource_type' => hes_resource_type,
                                  'units' => to_units }
      end
    end

    # Calculate the source energy
    total_source_energy, asset_source_energy = calc_source_energy(runner, outputs, units_map)
    { 'total_source_energy' => total_source_energy,
      'asset_source_energy' => asset_source_energy }.each do |resource_type, quantity|
      quantity = quantity.round(2)
      json_data['end_use'] << { 'quantity' => quantity,
                                'period_type' => 'year',
                                'resource_type' => resource_type,
                                'units' => 'MBtu' }
      runner.registerValue(resource_type, quantity)
      runner.registerInfo("Registering #{quantity} for #{resource_type}.")
    end

    # Calculate the carbon emissions
    carbon_emissions = calc_carbon_emissions(runner, outputs, hpxml.header.state_code)
    resource_type = 'carbon_emissions'
    json_data['end_use'] << { 'quantity' => carbon_emissions,
                              'period_type' => 'year',
                              'resource_type' => resource_type,
                              'units' => 'lb' }
    runner.registerValue(resource_type, carbon_emissions)
    runner.registerInfo("Registering #{carbon_emissions} for #{resource_type}.")

    # Calculate utility cost
    utility_cost = calc_utility_cost(runner, outputs, hpxml.header.state_code)
    resource_type = 'utility_cost'
    json_data['end_use'] << { 'quantity' => utility_cost,
                              'period_type' => 'year',
                              'resource_type' => resource_type,
                              'units' => 'USD' }
    runner.registerValue(resource_type, utility_cost)
    runner.registerInfo("Registering #{utility_cost} for #{resource_type}.")

    # Calculate the score
    weather_station = hpxml.climate_and_risk_zones.weather_station_wmo.to_i
    runner.registerValue('weather_station', weather_station)
    runner.registerInfo("Registering #{weather_station} for weather_station.")
    score = calc_score(runner, weather_station, asset_source_energy)
    resource_type = 'score'
    json_data['end_use'] << { 'quantity' => score,
                              'resource_type' => resource_type }
    runner.registerValue(resource_type, score)
    runner.registerInfo("Registering #{score} for #{resource_type}.")

    # Calculate cost metrics (e.g., sqft, capacity)
    cost_multipliers = calc_cost_multipliers(hpxml)
    cost_multipliers.each do |key, value|
      end_use, units = key
      json_data['end_use'] << { 'quantity' => value,
                                'resource_type' => 'cost_multiplier',
                                'end_use' => end_use,
                                'units' => units }
    end

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

  def retrieve_hescore_outputs(monthly_csv_path, units_map)
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
    return outputs
  end

  def calc_source_energy(runner, outputs, units_map)
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
      if hes_end_use == 'generation'
        # PV generation gets a site energy credit for _asset_ source energy (and score)
        asset_site_to_source_factor = -1.0
        total_site_to_source_factor = -1.0 * site_to_source_map[hes_resource_type]
      else
        asset_site_to_source_factor = site_to_source_map[hes_resource_type]
        total_site_to_source_factor = site_to_source_map[hes_resource_type]
      end
      next if total_site_to_source_factor.nil?

      units = units_map[hes_resource_type]
      total_source_energy += UnitConversions.convert(values.sum, units, 'MBtu') * total_site_to_source_factor

      next unless ['heating', 'cooling', 'hot_water', 'generation'].include? hes_end_use

      asset_source_energy += UnitConversions.convert(values.sum, units, 'MBtu') * asset_site_to_source_factor
    end
    return total_source_energy, asset_source_energy
  end

  def calc_carbon_emissions(runner, outputs, state_code)
    fuel_conv = { 'electric' => 1.0, # kWh -> kWh
                  'natural_gas' => 1.0, # kBtu -> kBtu
                  'lpg' => 1.0, # kBtu -> kBtu
                  'fuel_oil' => 1.0, # kBtu -> kBtu
                  'cord_wood' => 1.0, # kBtu -> kBtu
                  'pellet_wood' => 1.0 } # kBtu -> kBtu
    carbon_factors = get_lookup_values_by_state(runner, state_code, 'lu_carbon_factor_by_state.csv')
    fuel_uses = {}
    outputs.each do |hes_key, values|
      hes_end_use, hes_resource_type = hes_key
      next if fuel_conv[hes_resource_type].nil?

      fuel_uses[hes_resource_type] = 0.0 if fuel_uses[hes_resource_type].nil?
      if hes_end_use == 'generation'
        fuel_uses[hes_resource_type] -= values.sum * fuel_conv[hes_resource_type]
      else
        fuel_uses[hes_resource_type] += values.sum * fuel_conv[hes_resource_type]
      end
    end
    carbon_emissions = 0.0
    carbon_emissions += (fuel_uses['electric'] * Float(carbon_factors['electric (lb/kWh)']))
    carbon_emissions += (fuel_uses['natural_gas'] * Float(carbon_factors['natural_gas (lb/kBtu)']))
    carbon_emissions += (fuel_uses['lpg'] * Float(carbon_factors['lpg (lb/kBtu)']))
    carbon_emissions += (fuel_uses['fuel_oil'] * Float(carbon_factors['fuel_oil (lb/kBtu)']))
    carbon_emissions += (fuel_uses['cord_wood'] * Float(carbon_factors['cord_wood (lb/kBtu)']))
    carbon_emissions += (fuel_uses['pellet_wood'] * Float(carbon_factors['pellet_wood (lb/kBtu)']))
    return carbon_emissions.round(0)
  end

  def calc_utility_cost(runner, outputs, state_code)
    fuel_conv = { 'electric' => 1.0, # kWh -> kWh
                  'natural_gas' => 1.0 / 100.0, # kBtu -> therm
                  'lpg' => 10000.0 / 916000.0, # kBtu -> gal, assuming 0.0916 MMBtu/gal
                  'fuel_oil' => 10000.0 / 1385000.0, # kBtu -> gal, assuming 0.1385 MMBtu/gal
                  'cord_wood' => 1.0 / 20000.0, # kBtu -> cord, assuming 20 MMBtu/cord
                  'pellet_wood' => 2.0 / 16.4 } # kBtu -> lb, assuming 16.4 MMBtu/ton and 2000 lb/ton
    resource_prices = get_lookup_values_by_state(runner, state_code, 'lu_resource_price_by_state.csv')
    fuel_uses = {}
    outputs.each do |hes_key, values|
      hes_end_use, hes_resource_type = hes_key
      next if fuel_conv[hes_resource_type].nil?

      fuel_uses[hes_resource_type] = 0.0 if fuel_uses[hes_resource_type].nil?
      if hes_end_use == 'generation'
        fuel_uses[hes_resource_type] -= values.sum * fuel_conv[hes_resource_type]
      else
        fuel_uses[hes_resource_type] += values.sum * fuel_conv[hes_resource_type]
      end
    end
    utility_cost = 0.0
    utility_cost += ([fuel_uses['electric'], 0.0].max * Float(resource_prices['electric ($/kWh)'])) # max used to zero out PV annual excess
    utility_cost += (fuel_uses['natural_gas'] * Float(resource_prices['natural_gas ($/therm)']))
    utility_cost += (fuel_uses['lpg'] * Float(resource_prices['lpg ($/gallon)']))
    utility_cost += (fuel_uses['fuel_oil'] * Float(resource_prices['fuel_oil ($/gallon)']))
    utility_cost += (fuel_uses['cord_wood'] * Float(resource_prices['cord_wood ($/cord)']))
    utility_cost += (fuel_uses['pellet_wood'] * Float(resource_prices['pellet_wood ($/lb)']))
    return utility_cost.round(2)
  end

  def calc_score(runner, weather_station, asset_source_energy)
    bins_file = File.join(File.dirname(__FILE__), '..', '..', 'resources', 'bins.csv')
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
    fail "Unable to find weather station '#{weather_station}' in bins.csv."
    return score
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

  def get_lookup_values_by_state(runner, state_code, csv_file_name)
    csv_file = File.join(File.dirname(__FILE__), '..', '..', 'resources', csv_file_name)
    CSV.foreach(csv_file, headers: true) do |row|
      if row['abbreviation'] == state_code
        return row.to_h
      end
    end
    fail "Unable to find state '#{state_code}' in #{csv_file_name}."
  end

  def calc_cost_multipliers(hpxml)
    # Initialize all possible cost multipliers so that we throw an
    # error if we encounter an unexpected key below.
    #          [end_use, units] => cost_multiplier_value
    values = { ['footprint_area', 'sqft'] => 0.0,
               ['conditioned_floor_area', 'sqft'] => 0.0,
               ['floor1_floor_area', 'sqft'] => 0.0,
               ['floor2_floor_area', 'sqft'] => 0.0,
               ['floor1_wall_area', 'sqft'] => 0.0,
               ['floor2_wall_area', 'sqft'] => 0.0,
               ['roof1_ceiling_area', 'sqft'] => 0.0,
               ['roof2_ceiling_area', 'sqft'] => 0.0,
               ['roof1_kneewall_area', 'sqft'] => 0.0,
               ['roof2_kneewall_area', 'sqft'] => 0.0,
               ['roof1_roof_area', 'sqft'] => 0.0,
               ['roof2_roof_area', 'sqft'] => 0.0,
               ['roof1_skylight_area', 'sqft'] => 0.0,
               ['roof2_skylight_area', 'sqft'] => 0.0,
               ['front_wall_area', 'sqft'] => 0.0,
               ['back_wall_area', 'sqft'] => 0.0,
               ['left_wall_area', 'sqft'] => 0.0,
               ['right_wall_area', 'sqft'] => 0.0,
               ['front_window_area', 'sqft'] => 0.0,
               ['back_window_area', 'sqft'] => 0.0,
               ['left_window_area', 'sqft'] => 0.0,
               ['right_window_area', 'sqft'] => 0.0,
               ['hvac1_duct1_area', 'sqft'] => 0.0,
               ['hvac1_duct2_area', 'sqft'] => 0.0,
               ['hvac1_duct3_area', 'sqft'] => 0.0,
               ['hvac2_duct1_area', 'sqft'] => 0.0,
               ['hvac2_duct2_area', 'sqft'] => 0.0,
               ['hvac2_duct3_area', 'sqft'] => 0.0,
               ['hvac1_cooling_capacity', 'Btuh'] => 0.0,
               ['hvac1_heating_capacity', 'Btuh'] => 0.0,
               ['hvac2_cooling_capacity', 'Btuh'] => 0.0,
               ['hvac2_heating_capacity', 'Btuh'] => 0.0,
               ['water_heater_capacity', 'gal'] => 0.0 }

    # Footprint area
    key = ['footprint_area', 'sqft']
    values[key] = hpxml.building_construction.building_footprint_area

    # Conditioned floor area
    key = ['conditioned_floor_area', 'sqft']
    values[key] = hpxml.building_construction.conditioned_floor_area

    # Enclosure surface areas
    (hpxml.frame_floors +
     hpxml.slabs +
     hpxml.roofs +
     hpxml.walls +
     hpxml.windows +
     hpxml.skylights +
     hpxml.foundation_walls).each do |surface|
      instance_id = surface.id.split('_')[0]
      if surface.is_a? HPXML::Wall
        if surface.exterior_adjacent_to == HPXML::LocationAtticVented
          instance_id += '_kneewall'
        else
          instance_id += '_wall'
        end
      elsif surface.is_a? HPXML::FoundationWall
        instance_id += '_wall'
      elsif surface.is_a? HPXML::Window
        instance_id += '_window'
      elsif surface.is_a? HPXML::Skylight
        instance_id += '_skylight'
      elsif surface.is_a? HPXML::FrameFloor
        next if surface.is_floor # We'll use slabs for floor areas to include slab-on-grade/conditioned basement

        instance_id += '_ceiling'
      elsif surface.is_a? HPXML::Slab
        instance_id += '_floor'
      elsif surface.is_a? HPXML::Roof
        instance_id += '_roof'
      else
        fail "Unexpected surface type: #{surface.class}"
      end
      key = ["#{instance_id}_area", 'sqft']
      values[key] += surface.area
    end

    # HVAC heating/cooling capacities
    hpxml.hvac_systems.each do |hvac_system|
      instance_id = hvac_system.id.split('_')[0]
      if hvac_system.respond_to? :heating_capacity
        key = ["#{instance_id}_heating_capacity", 'Btuh']
        values[key] += hvac_system.heating_capacity
      end
      if hvac_system.respond_to? :cooling_capacity
        key = ["#{instance_id}_cooling_capacity", 'Btuh']
        values[key] += hvac_system.cooling_capacity
      end
    end

    # HVAC duct areas
    hpxml.hvac_distributions.each do |hvac_dist|
      hvac_instance_id = hvac_dist.hvac_systems[0].id.split('_')[0]
      hvac_dist.ducts.each do |duct|
        duct_instance_id = duct.id.split('_')[0]
        key = ["#{hvac_instance_id}_#{duct_instance_id}_area", 'sqft']
        values[key] += duct.duct_surface_area
      end
    end

    # Water heater capacity
    key = ['water_heater_capacity', 'gal']
    values[key] = hpxml.water_heating_systems[0].tank_volume.to_f

    # Round values
    values.each do |key, val|
      values[key] = val.round(0)
    end

    return values
  end
end

# register the measure to be used by the application
ReportHEScoreOutput.new.registerWithApplication
