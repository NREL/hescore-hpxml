Generation
##########

Solar Electric
**************

HEScore allows for a single photovoltaic system to be included as of v2016.
In HPXML, multiple ``PVSystem`` elements can be specified to represent the PV systems on the house.
The translator combines multiple systems and generates the appropriate HEScore inputs as follows:

DC Capacity
===========

Because there is no input for number of panels in HPXML, the ``capacity_known`` input for HEScore is always true.
The ``system_capacity`` in HEScore is calculated by summing all the ``MaxPowerOutput`` elements in HPXML.
A ``MaxPowerOutput`` is required for every ``PVSystem``.

Year Installed
==============

For each ``PVSystem`` the ``YearInverterManufactured`` and ``YearModulesManufactured`` element values are retrieved,
and the larger of the two is assumed to be the year that system was installed.
When there are multiple ``PVSystem`` elements, a capacity-weighted average of the assumed year installed is calculated and used.

Panel Orientation (Azimuth)
===========================

For each ``PVSystem`` the ``ArrayAzimuth`` (degrees clockwise from north) is retrieved.
If ``ArrayAzimuth`` is not available ``ArrayOrientation`` (north, northwest, etc) is converted into an azimuth.
A capacity-weighted average azimuth is calculated and converted into the nearest cardinal direction (north, northwest, etc)
for submission into the ``array_azimuth`` HEScore input (which expects a direction, not a numeric azimuth).
