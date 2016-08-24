Domestic Hot Water
##################

.. contents:: Table of Contents

Determining the primary water heating system
********************************************

HPXML allows for the specification of several ``WaterHeatingSystem`` elements.
HEScore only allows one to be specified. If there are more than one water
heaters present in the HPXML file, the one that serves the largest fraction of
the the load is selected based on the value of ``FractionDHWLoadServed``. If
not all of the ``WaterHeatingSystem`` elements have ``FractionDHWServed``
subelements (or if none of them do), the first ``WaterHeatingSystem`` is
selected.

Water heater type
*****************

The water heater type is mapped from HPXML to HEScore accordingly:

.. table:: HPXML to HEScore water heater type mapping
   
   +----------------------------------------+---------------------------------+
   |HPXML                                   |HEScore                          |
   +----------------------------------------+----------------+----------------+
   |WaterHeaterType                         |DHW Category    |DHW Type        |
   +========================================+================+================+
   |storage water heater                    |unit            |storage         |
   +----------------------------------------+                |                |
   |dedicated boiler with storage tank      |                |                |
   +----------------------------------------+                |                |
   |instantaneous water heater [#f1]_       |                |                |
   +----------------------------------------+----------------+----------------+
   |heat pump water heater                  |unit            |heat_pump       |
   +----------------------------------------+----------------+----------------+
   |space-heating boiler with storage tank  |combined        |indirect        |
   +----------------------------------------+----------------+----------------+
   |space-heating boiler with tankless coil |combined        |tankless_coil   |
   +----------------------------------------+----------------+----------------+

The fuel type is mapped according to the same mapping used in
:ref:`fuel-mapping`.

Water heating efficiency
************************

If the ``WaterHeatingSystem/EnergyFactor`` element exists, that energy factor is
sent to HEScore. When an energy factor cannot be found, HEScore can accept the
year the equipment was installed and estimate the efficiency based on that. The
year is retrieved from the ``YearInstalled`` element, and if that is not
present the ``ModelYear`` element.


.. rubric:: Footnotes

.. [#f1] The HEScore help instructs, "If the water heater is a tankless model (aka: on-demand or instantaneous water heater) it should be characterized the same as a storage model that uses the same fuel. An electric tankless should be entered as Electric Storage, a natural gas tankless should be entered as Natural Gas Storage, and an LPG or propane tankless should be entered as LPG Storage."
