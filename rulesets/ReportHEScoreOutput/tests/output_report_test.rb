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
      'floor1_floor_area' => 1000, # sqft
      'floor2_floor_area' => 0, # sqft
      'floor1_wall_area' => 0, # sqft
      'floor2_wall_area' => 0, # sqft
      'roof1_ceiling_area' => 1000, # sqft
      'roof2_ceiling_area' => 0, # sqft
      'roof1_kneewall_area' => 0, # sqft
      'roof2_kneewall_area' => 0, # sqft
      'roof1_roof_area' => 1154, # sqft
      'roof2_roof_area' => 0, # sqft
      'roof1_skylight_area' => 0, # sqft
      'roof2_skylight_area' => 0, # sqft
      'front_wall_area' => 653, # sqft
      'back_wall_area' => 653, # sqft
      'left_wall_area' => 392, # sqft
      'right_wall_area' => 392, # sqft
      'front_window_area' => 60, # sqft
      'back_window_area' => 50, # sqft
      'left_window_area' => 30, # sqft
      'right_window_area' => 40, # sqft
      'hvac1_duct1_area' => 1102, # sqft
      'hvac1_duct2_area' => 0, # sqft
      'hvac1_duct3_area' => 0, # sqft
      'hvac2_duct1_area' => 0, # sqft
      'hvac2_duct2_area' => 0, # sqft
      'hvac2_duct3_area' => 0, # sqft
      'hvac1_cooling_capacity' => 32031, # Btuh
      'hvac1_heating_capacity' => 61028, # Btuh
      'hvac2_cooling_capacity' => 0, # Btuh
      'hvac2_heating_capacity' => 0, # Btuh
      'water_heater_capacity' => 40 # gal
    }
    base_expected_values.each do |end_use, expected_value|
      assert_equal(expected_value, actual_values[end_use])
    end

    # Floor_unconditioned_basement.json: Check floor1_wall_area
    json_path = File.join(@regression_files_path, 'Floor_unconditioned_basement.json')
    actual_values = _test_measure(json_path)
    expected_values = base_expected_values.dup
    expected_values['floor1_wall_area'] = 1045
    expected_values['hvac1_cooling_capacity'] = 37187
    expected_values['hvac1_heating_capacity'] = 60396
    expected_values.each do |end_use, expected_value|
      assert_equal(expected_value, actual_values[end_use])
    end

    # Floor2_vented_crawl.json: Check floor2_floor_area, floor2_wall_area
    json_path = File.join(@regression_files_path, 'Floor2_vented_crawl.json')
    actual_values = _test_measure(json_path)
    expected_values = base_expected_values.dup
    expected_values['floor1_floor_area'] = 600
    expected_values['floor2_floor_area'] = 400
    expected_values['floor2_wall_area'] = 143
    expected_values['hvac1_cooling_capacity'] = 33639
    expected_values['hvac1_heating_capacity'] = 60343
    expected_values.each do |end_use, expected_value|
      assert_equal(expected_value, actual_values[end_use])
    end

    # Roof_knee_wall.json: Check roof1_kneewall_area, roof2_roof_area
    json_path = File.join(@regression_files_path, 'Roof_knee_wall.json')
    actual_values = _test_measure(json_path)
    expected_values = base_expected_values.dup
    expected_values['roof1_ceiling_area'] = 600
    expected_values['roof1_roof_area'] = 692
    expected_values['roof1_kneewall_area'] = 200
    expected_values['roof2_roof_area'] = 400
    expected_values['hvac1_cooling_capacity'] = 32309
    expected_values['hvac1_heating_capacity'] = 61912
    expected_values.each do |end_use, expected_value|
      assert_equal(expected_value, actual_values[end_use])
    end

    # Skylight_dcaa_and_dtaa.json: Check roof2_ceiling_area, roof1_skylight_area, roof2_skylight_area
    json_path = File.join(@regression_files_path, 'Skylight_dcaa_and_dtaa.json')
    actual_values = _test_measure(json_path)
    expected_values = base_expected_values.dup
    expected_values['roof1_ceiling_area'] = 600
    expected_values['roof1_roof_area'] = 692
    expected_values['roof1_skylight_area'] = 100
    expected_values['roof2_ceiling_area'] = 400
    expected_values['roof2_roof_area'] = 462
    expected_values['roof2_skylight_area'] = 40
    expected_values['hvac1_cooling_capacity'] = 72841
    expected_values['hvac1_heating_capacity'] = 72136
    expected_values.each do |end_use, expected_value|
      assert_equal(expected_value, actual_values[end_use])
    end

    # Duct_multiple.json: Check hvac1_duct2_area
    json_path = File.join(@regression_files_path, 'Duct_multiple.json')
    actual_values = _test_measure(json_path)
    expected_values = base_expected_values.dup
    expected_values['floor1_wall_area'] = 1045
    expected_values['hvac1_duct1_area'] = 790
    expected_values['hvac1_duct2_area'] = 474
    expected_values['hvac1_cooling_capacity'] = 35894
    expected_values['hvac1_heating_capacity'] = 58197
    expected_values.each do |end_use, expected_value|
      assert_equal(expected_value, actual_values[end_use])
    end

    # HVAC2.json: Check hvac2_duct1_area, hvac2_cooling_capacity, hvac2_heating_capacity
    json_path = File.join(@regression_files_path, 'HVAC2.json')
    actual_values = _test_measure(json_path)
    expected_values = base_expected_values.dup
    expected_values['hvac2_duct1_area'] = 551
    expected_values['hvac1_cooling_capacity'] = 26103
    expected_values['hvac1_heating_capacity'] = 47562
    expected_values['hvac2_cooling_capacity'] = 21091
    expected_values['hvac2_heating_capacity'] = 21091
    expected_values.each do |end_use, expected_value|
      assert_equal(expected_value, actual_values[end_use])
    end
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
end
