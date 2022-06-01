v6.2 to v7.0
############

This release is coordinated with `OpenStudio-HEScore
v2.0 <https://github.com/NREL/OpenStudio-HEScore/releases/tag/v2.0>`_.

What's New
==========

Envelope
--------

-  EPS wall type will now be selected if there is any continuous insulation on
   the wall, not just if it has the ``InsulationMaterial/Rigid`` subelement. See
   :ref:`wood-frame-walls`.
-  Assembly R-values can be used in for :ref:`floors <floor-insulation>`,
   :ref:`attics <attic-rvalues>`, :ref:`roofs <roof-rvalues>`, and :ref:`walls
   <wall-construction>`. 
-  More R-values are now available in the HEScore construction codes for floors,
   attics, roofs, and walls. No action is required. Existing HPXML elements will
   be translated accordingly.
-  A blower door test no longer requires the
   ``AirInfiltrationMeasurement/TypeOfInfiltrationMeasurement`` element. If a
   CFM50 or ACH50 value is reported, it will be used. See :ref:`blower-door-test`.
-  Added support for knee walls. See :ref:`knee-walls`.
-  Either an ``AirInfiltrationMeasurement`` or ``AirSealingMeasurement`` element
   is now required.
-  Ducts in the garage will now be translated to unvented crawlspace in HEScore.
   See :ref:`ductlocationmapping`.

HVAC
----

-  Insulated ducts can now be specified by either the
   ``DuctInsulationThickness`` or the ``DuctInsulationMaterial`` elements. See
   :ref:`duct-insulation`.
-  Additional duct locations are now available. See :ref:`ductlocationmapping`.
-  Duct blaster measurements can be used to describe duct leakage. See :ref:`duct-leakage-measurements`.

Water Heating
-------------

-  The maximum allowed EF for a tank type water heater is now 0.95, and the
   maximum allowed EF for a tankless water heater is 0.99. Electric heat pump
   water heaters will continue to allow EFs between 1.0 and 4.0 inclusive.

PV
--

-  PV Tilt is translated and used in HEScore. See :ref:`panel-tilt`.
-  Number of Panels is now being translated from HPXML v3 files. See
   :ref:`number-of-panels`.

Changelog
=========

-  Move external_building_id to building_address element by `@bpark1327 <https://github.com/bpark1327>`_
   in `#149 <https://github.com/NREL/hescore-hpxml/pull/149>`_
-  Update issue templates by `@nmerket <https://github.com/nmerket>`_ in
   `#153 <https://github.com/NREL/hescore-hpxml/pull/153>`_
-  Adding github workflow for CI by `@nmerket <https://github.com/nmerket>`_ in
   `#154 <https://github.com/NREL/hescore-hpxml/pull/154>`_
-  Ignoring gable walls in hpxml v3 files by `@nmerket <https://github.com/nmerket>`_ in
   `#152 <https://github.com/NREL/hescore-hpxml/pull/152>`_
-  JSON Schema by `@bpark1327 <https://github.com/bpark1327>`_ in
   `#144 <https://github.com/NREL/hescore-hpxml/pull/144>`_
-  Failing CI on broken tests for all versions by `@nmerket <https://github.com/nmerket>`_ in
   `#159 <https://github.com/NREL/hescore-hpxml/pull/159>`_
-  Wall translation fixes and water heater EF rounding by `@bpark1327 <https://github.com/bpark1327>`_ in
   `#164 <https://github.com/NREL/hescore-hpxml/pull/164>`_
-  Update duct insulation mapping by `@bpark1327 <https://github.com/bpark1327>`_ in
   `#163 <https://github.com/NREL/hescore-hpxml/pull/163>`_
-  JSON Schema, take 2 by `@bpark1327 <https://github.com/bpark1327>`_ in
   `#161 <https://github.com/NREL/hescore-hpxml/pull/161>`_
-  Handle zip+4 in hpxml by `@nmerket <https://github.com/nmerket>`_ in
   `#169 <https://github.com/NREL/hescore-hpxml/pull/169>`_
-  not allowing R-value to go past zero for walls with XPS by `@nmerket <https://github.com/nmerket>`_
   in `#170 <https://github.com/NREL/hescore-hpxml/pull/170>`_
-  PV Tilt by `@shorowit <https://github.com/shorowit>`_ in
   `#172 <https://github.com/NREL/hescore-hpxml/pull/172>`_
-  Update schema for townhouse walls by `@bpark1327 <https://github.com/bpark1327>`_ in
   `#175 <https://github.com/NREL/hescore-hpxml/pull/175>`_
-  PV Number of Panels by `@nmerket <https://github.com/nmerket>`_ in
   `#179 <https://github.com/NREL/hescore-hpxml/pull/179>`_
-  Additional duct locations by `@shorowit <https://github.com/shorowit>`_ in
   `#177 <https://github.com/NREL/hescore-hpxml/pull/177>`_
-  Duct blaster measurements by `@bpark1327 <https://github.com/bpark1327>`_ in
   `#168 <https://github.com/NREL/hescore-hpxml/pull/168>`_
-  Update hpxml2hescore duct validation by `@bpark1327 <https://github.com/bpark1327>`_ in
   `#173 <https://github.com/NREL/hescore-hpxml/pull/173>`_
-  Update duct blaster measurement by `@bpark1327 <https://github.com/bpark1327>`_ in
   `#183 <https://github.com/NREL/hescore-hpxml/pull/183>`_
-  Adding effective R-value lookup by `@nmerket <https://github.com/nmerket>`_ in
   `#160 <https://github.com/NREL/hescore-hpxml/pull/160>`_
-  Low-e storms by `@bpark1327 <https://github.com/bpark1327>`_ in
   `#176 <https://github.com/NREL/hescore-hpxml/pull/176>`_
-  CEE HVAC efficiency levels by `@yzhou601 <https://github.com/yzhou601>`_ in
   `#185 <https://github.com/NREL/hescore-hpxml/pull/185>`_
-  Increase granularity of construction codes by `@bpark1327 <https://github.com/bpark1327>`_ in
   `#187 <https://github.com/NREL/hescore-hpxml/pull/187>`_
-  Improve air infiltration measurement translation by `@bpark1327 <https://github.com/bpark1327>`_ in
   `#190 <https://github.com/NREL/hescore-hpxml/pull/190>`_
-  Knee walls by `@nmerket <https://github.com/nmerket>`_ in
   `#184 <https://github.com/NREL/hescore-hpxml/pull/184>`_
-  Fix inappropriate water heater EFs by `@bpark1327 <https://github.com/bpark1327>`_ in
   `#191 <https://github.com/NREL/hescore-hpxml/pull/191>`_
-  Remove old wall construction codes by `@bpark1327 <https://github.com/bpark1327>`_ in
   `#195 <https://github.com/NREL/hescore-hpxml/pull/195>`_
-  Improve multiple ducts translation by `@bpark1327 <https://github.com/bpark1327>`_ in
   `#194 <https://github.com/NREL/hescore-hpxml/pull/194>`_
-  Improve air infiltration measurement translation, Take 2 by
   `@bpark1327 <https://github.com/bpark1327>`_ in `#193 <https://github.com/NREL/hescore-hpxml/pull/193>`_
-  Updating garage duct location to unvented_crawl by `@nmerket <https://github.com/nmerket>`_ in
   `#197 <https://github.com/NREL/hescore-hpxml/pull/197>`_

**Full Changelog**:
https://github.com/NREL/hescore-hpxml/compare/v6.2..v7.0
