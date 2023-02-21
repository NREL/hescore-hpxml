# frozen_string_literal: true

require_relative '../../../hpxml-measures/HPXMLtoOpenStudio/resources/minitest_helper'
require 'openstudio'
require 'openstudio/measure/ShowRunnerOutput'
require 'fileutils'
require 'json'

class ReportHEScoreOutputTest < MiniTest::Test
  def setup
    @root_path = File.absolute_path(File.join(File.dirname(__FILE__), '..', '..', '..'))
    @regression_files_path = File.join(@root_path, 'workflow', 'regression_files')

    @tmp_output_path = File.join(@root_path, 'workflow', 'tmp_output')
    FileUtils.mkdir_p(@tmp_output_path)
  end

  def teardown
    FileUtils.rm_rf(@tmp_output_path)
  end

  def test_cost_multipliers
    # Base.json
    json_path = File.join(@regression_files_path, 'Base.json')
    actual_values = _test_measure(json_path)
    base_expected_values = {
      'footprint_area' => 1000, # sqft
      'conditioned_floor_area' => 2000, # sqft
      'floor1_floor_area' => 1000, # sqft
      'floor2_floor_area' => 0, # sqft
      'floor1_wall_area' => 0, # sqft
      'floor2_wall_area' => 0, # sqft
      'roof1_ceiling_area' => 1000, # sqft
      'roof2_ceiling_area' => 0, # sqft
      'roof1_kneewall_area' => 0, # sqft
      'roof2_kneewall_area' => 0, # sqft
      'roof1_roof_area' => 1155, # sqft
      'roof2_roof_area' => 0, # sqft
      'roof1_skylight_area' => 0, # sqft
      'roof2_skylight_area' => 0, # sqft
      'front_wall_area' => 538, # sqft
      'back_wall_area' => 528, # sqft
      'left_wall_area' => 508, # sqft
      'right_wall_area' => 518, # sqft
      'front_window_area' => 60, # sqft
      'back_window_area' => 50, # sqft
      'left_window_area' => 30, # sqft
      'right_window_area' => 40, # sqft
      'hvac1_duct1_area' => 551, # sqft
      'hvac1_duct2_area' => 0, # sqft
      'hvac1_duct3_area' => 0, # sqft
      'hvac2_duct1_area' => 0, # sqft
      'hvac2_duct2_area' => 0, # sqft
      'hvac2_duct3_area' => 0, # sqft
      'water_heater_capacity' => 40, # gal
      'hvac1_cooling_capacity' => 32000, # Btuh
      'hvac1_heating_capacity' => 60000, # Btuh
      'hvac2_cooling_capacity' => 0, # Btuh
      'hvac2_heating_capacity' => 0, # Btuh
    }
    _check_values(base_expected_values, actual_values)

    # Roof_type_cathedral_ceiling.json
    json_path = File.join(@regression_files_path, 'Roof_type_cathedral_ceiling.json')
    actual_values = _test_measure(json_path)
    expected_values = base_expected_values.dup
    expected_values['roof1_ceiling_area'] = 0
    expected_values['roof1_roof_area'] = 1000
    expected_values['hvac1_duct1_area'] = 0
    expected_values['hvac1_cooling_capacity'] = 30000
    expected_values['hvac1_heating_capacity'] = 58000
    _check_values(expected_values, actual_values)

    # Floor_conditioned_basement.json
    json_path = File.join(@regression_files_path, 'Floor_conditioned_basement.json')
    actual_values = _test_measure(json_path)
    expected_values = base_expected_values.dup
    expected_values['footprint_area'] = 500
    expected_values['floor1_wall_area'] = 739
    expected_values['front_wall_area'] = 385
    expected_values['back_wall_area'] = 375
    expected_values['left_wall_area'] = 355
    expected_values['right_wall_area'] = 365
    expected_values['hvac1_cooling_capacity'] = 35000
    expected_values['hvac1_heating_capacity'] = 58000
    _check_values(expected_values, actual_values)

    # Full_for_cost_multipliers.json
    json_path = File.join(@regression_files_path, 'Full_for_cost_multipliers.json')
    actual_values = _test_measure(json_path)
    expected_values = {
      'footprint_area' => 1000, # sqft
      'conditioned_floor_area' => 2000, # sqft
      'floor1_floor_area' => 600, # sqft
      'floor2_floor_area' => 400, # sqft
      'floor1_wall_area' => 588, # sqft
      'floor2_wall_area' => 143, # sqft
      'roof1_ceiling_area' => 600, # sqft
      'roof2_ceiling_area' => 400, # sqft
      'roof1_kneewall_area' => 100, # sqft
      'roof2_kneewall_area' => 200, # sqft
      'roof1_roof_area' => 693, # sqft
      'roof2_roof_area' => 462, # sqft
      'roof1_skylight_area' => 100, # sqft
      'roof2_skylight_area' => 40, # sqft
      'front_wall_area' => 538, # sqft
      'back_wall_area' => 528, # sqft
      'left_wall_area' => 508, # sqft
      'right_wall_area' => 518, # sqft
      'front_window_area' => 60, # sqft
      'back_window_area' => 50, # sqft
      'left_window_area' => 30, # sqft
      'right_window_area' => 40, # sqft
      'hvac1_duct1_area' => 277, # sqft
      'hvac1_duct2_area' => 166, # sqft
      'hvac1_duct3_area' => 0, # sqft
      'hvac2_duct1_area' => 118, # sqft
      'hvac2_duct2_area' => 71, # sqft
      'hvac2_duct3_area' => 0, # sqft
      'water_heater_capacity' => 40, # gal
      'hvac1_cooling_capacity' => 62000, # Btuh
      'hvac1_heating_capacity' => 61000, # Btuh
      'hvac2_cooling_capacity' => 27000, # Btuh
      'hvac2_heating_capacity' => 27000, # Btuh
    }
    _check_values(expected_values, actual_values)
  end

  def _test_measure(json_path)
    # Run measure via run_simulation.rb
    run_rb = File.join(@root_path, 'workflow', 'run_simulation.rb')
    success = system("\"#{OpenStudio.getOpenStudioCLI}\" \"#{run_rb}\" -j \"#{json_path}\" -o \"#{@tmp_output_path}\"")
    assert_equal(true, success)

    # Check for output
    output_path = File.join(@tmp_output_path, 'results', 'results.json')
    assert(File.exist? output_path)

    # Return JSON output cost multipliers
    json_output = JSON.parse(File.read(output_path))
    cost_multipliers = {}
    json_output['end_use'].each do |end_use|
      next if end_use['resource_type'] != 'cost_multiplier'

      cost_multipliers[end_use['end_use']] = end_use['quantity']
    end
    return cost_multipliers
  end

  def _check_values(expected_values, actual_values)
    # Check for exact matches
    expected_values.each do |end_use, expected_value|
      if (end_use.include? 'capacity') && (expected_value > 0)
        # Check HVAC capacity is within half a ton
        assert_in_delta(expected_value, actual_values[end_use], 6000)
      else
        # Check for exact value
        assert_equal(expected_value, actual_values[end_use])
      end
    end
  end
end
