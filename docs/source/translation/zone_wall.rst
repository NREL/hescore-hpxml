Walls
#####

.. contents:: Table of Contents

.. _wallorientation:

Wall Orientation
****************

The flexibility of HPXML allows specification of any number of walls and windows
facing any direction. HEScore expects only one wall/window specification for
each side of the building (front, back, left, right). Simplifying the almost
infinite flexibility of HPXML in this regard presents some challenges.  

For each wall in the HPXML document, the translator attempts to assign the wall
to the nearest side of the building, which is relative to the orientation of
the front of the building. Then the properties of the largest wall by area on
each side of the building are then used to define the wall construction sent to
HEScore. If there is only one wall on any side of the house, the area is not
required for that side. 

HEScore also allows the specification of one wall for the entire building. If
none of the walls in HPXML have orientation (or azimuth) data the largest wall
is selected and the properties of that wall are used to define the wall
construction for the whole building. If there is only one wall and no area
specified that wall is used to determine the wall construction.

.. warning::

   There are several potential situations in the wall orientation handling that
   can cause this to error including:
   
   #. A wall falls exactly between two sides of the house (i.e. The front of
      the house faces North and one of the walls faces Northeast.)
   #. The largest wall cannot be determined for a side of the building or the
      whole building because one of the walls does not have an area. 
   #. Some of the walls have an orientation/azimuth and others don't.

Wall Construction
*****************

HEScore uses a selection of `construction codes`_ to describe wall construction
type, insulation levels, and siding. HPXML, as usual, uses a more flexible
approach defining wall types: layers of insulation materials that each include
an R-value, thickness, wall cavity information, etc. To translate the inputs
from HPXML to HEScore approximations need to be made to condense the continuous
inputs in HPXML to discrete inputs required for HEScore.

.. _construction codes: https://docs.google.com/spreadsheet/pub?key=0Avk3IqpWXaRkdGR6cXFwdVJ4ZVdYX25keDVEX1pPYXc&output=html

Wood Frame Walls
================

If ``WallType/WoodStud`` is selected in HPXML, each layer of the wall insulation
is parsed and if a rigid and continuous layer is found, or if the subelement
``WallType/WoodStud/ExpandedPolyStyreneSheathing`` is found, the wall is
specified in HEScore as "Wood Frame with Rigid Foam Sheathing."

.. code-block:: xml
   :emphasize-lines: 6,12,14

   <Wall>
      <SystemIdentifier id="wall1"/>
      <WallType>
          <WoodStud>
              <!-- Either this element needs to be here or continuous insulation below -->
              <ExpandedPolystyreneSheathing>true</ExpandedPolystyreneSheathing>
          </WoodStud>
      </WallType>
      <Insulation>
          <SystemIdentifier id="wall1ins"/>
          <Layer>
              <InstallationType>continuous</InstallationType>
              <InsulationMaterial>
                  <Rigid>eps</Rigid>
                  <!-- This can have any of the valid enumerations for this element, 
                       it only cares if the Rigid element is present. -->
              </InsulationMaterial>
          </Layer>
          ...
      </Insulation>
   </Wall>

Otherwise, if the ``OptimumValueEngineering`` boolean element is set to
``true``, the "Wood Frame with Optimal Value Engineering" wall type in HEScore
is selected. 

.. code-block:: xml
   :emphasize-lines: 5
   
   <Wall>
      <SystemIdentifier id="wall2"/>
      <WallType>
          <WoodStud>
              <OptimumValueEngineering>true</OptimumValueEngineering>
          </WoodStud>
          <Insulation>
              ...
          </Insulation>
      </WallType>
   </Wall>


.. note::

   The ``OptimumValueEngineering`` flag needs to be set in HPXML to
   translate to this wall type. The translator will not infer this from stud
   spacing.

Finally, if neither of the above conditions are met, the wall is specified as
simply "Wood Frame" in HEScore. 

In all cases the cavity R-value is summed for all insulation layers and the
nearest discrete R-value from the list of possible R-values for that wall type
is used.

The siding is selected according to the :ref:`siding map <sidingmap>`.

Structural Brick
================

If ``WallType/StructuralBrick`` is found in HPXML, one of the structural brick
codes in HEScore is specified. The nearest R-value to the sum of all the
insulation layer nominal R-values is selected.

.. code-block:: xml
   :emphasize-lines: 4,9,12

   <Wall>
      <SystemIdentifier id="wall3"/>
      <WallType>
          <StructuralBrick/>
      </WallType>
      <Insulation>
          <SystemIdentifier id="wall3ins"/>
          <Layer>
              <NominalRValue>5</NominalRValue>
          </Layer>
          <Layer>
              <NominalRValue>5</NominalRValue>
          </Layer>
          <!-- This would have a summed R-value of 10 -->
      </Insulation>
   </Wall>


Concrete Block or Stone
=======================

If ``WallType/ConcreteMasonryUnit`` or ``WallType/Stone`` is found, one of the
concrete block construction codes is used in HEScore. The nearest R-value to
the sum of all the insulation layer nominal R-values is selected. The siding is
translated using the :ref:`same assumptions as wood stud walls <sidingmap>`
with the exception that vinyl, wood, or aluminum siding is not available and if
those are specified in the HPXML an error will result.

Straw Bale
==========

If ``WallType/StrawBale`` is found in the HPXML wall, the straw bale wall
assembly code in HEScore is selected.

.. _sidingmap:

Siding
======

Siding mapping is done from the ``Wall/Siding`` element in HPXML. Siding is
specified as the last two characters of the construction code in HEScore.

.. table:: Siding type mapping

   ========================  ================
   HPXML                     HEScore 
   ========================  ================
   wood siding               wo
   stucco                    st
   synthetic stucco          st
   vinyl siding              vi
   aluminum siding           al
   brick veneer              br
   asbestos siding           *not translated*
   fiber cement siding       *not translated*
   composite shingle siding  *not translated*
   masonite siding           *not translated*
   other                     *not translated*
   ========================  ================   

.. note::

   *not translated* means the translation will fail for that house.

