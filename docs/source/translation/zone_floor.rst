Foundation Insulation
#####################

.. contents:: Table of Contents

Determining the primary foundation
**********************************

HEScore permits the specification of two foundations.
The two foundations that cover the largest area are selected.
This is determined by summing up the area of the ``FrameFloor`` or
``Slab`` elements (depending on what kind of foundation it is).
``Area`` elements are required for all foundations unless there is only one
foundation, then it is assumed to be the footprint area of the building.
If there are more than two foundations, the areas of the largest two are scaled
up to encompass the area of the remaining foundations while maintaining their
respective area fractions relative to each other.

Foundation Type
***************

Once a foundation is selected, the HEScore foundation type is selected from
HPXML according to the following table. 

.. table:: HPXML to HEScore foundation type mapping

   +----------------------+-------------------+-------------------------+
   |HPXML Foundation Type                     | HEScore Foundation Type |
   +======================+===================+=========================+
   |Basement              |Conditioned="true" |cond_basement            |
   +                      +-------------------+-------------------------+
   |                      |Conditioned="false"|uncond_basement          |
   |                      |or omitted         |                         |
   +----------------------+-------------------+-------------------------+
   |Crawlspace            |Vented="true"      |vented_crawl             |
   +                      +-------------------+-------------------------+
   |                      |Vented="false"     |unvented_crawl           |
   |                      |or omitted         |                         |
   +----------------------+-------------------+-------------------------+
   |SlabOnGrade                               |slab_on_grade            |
   +----------------------+-------------------+-------------------------+
   |Garage                                    |unvented_crawl           |
   +----------------------+-------------------+-------------------------+
   |AboveApartment                            |*not translated*         |
   +----------------------+-------------------+-------------------------+
   |Combination                               |*not translated*         |
   +----------------------+-------------------+-------------------------+
   |Ambient                                   |vented_crawl             |
   +----------------------+-------------------+-------------------------+
   |RubbleStone                               |*not translated*         |
   +----------------------+-------------------+-------------------------+
   |Other                                     |*not translated*         |
   +----------------------+-------------------+-------------------------+

.. warning::

   For foundation types that are *not translated* the translation will return an error.

Foundation wall insulation R-value
**********************************

If the foundation type is a basement or crawlspace, an area weighted average
R-value is calculated for the foundation walls. The area is obtained from the
``Area`` element, if present, or calculated from the ``Length`` and ``Height``
elements. The R-value is the sum of the
``FoundationWall/Insulation/Layer/NominalRValue`` element values for each
foundation wall. For each foundation wall, an effective R-value is looked up
based on the nearest R-value in the following table.

.. table:: Basement and crawlspace wall effective R-values

   =================  ==================
   Insulation Level   Effective R-value   
   =================  ==================
   R-0                4                   
   R-11               11.6                
   R-19               16.9               
   =================  ==================

Then a weighted average R-value is calculated by weighting the U-values by area.

.. math::
   :nowrap:

   \begin{align*}
   U_i &= \frac{1}{R_i} \\
   U_{eff,avg} &= \frac{\sum_i{U_i A_i}}{\sum_i A_i} \\
   R_{eff,avg} &= \frac{1}{U_{eff,avg}} \\
   \end{align*}

The effective R-value of the R-0 insulation level is then subtracted.

.. math::

   R = R_{eff,avg} - 4.0
   
Finally, the nearest insulation level is selected from the enumeration list.

Slab insulation R-value
***********************

If the foundation type is a slab on grade, an area weighted average R-value is
calculated using the value of ``ExposedPerimeter`` as the area. (The units work
out, the depth in the area drops out of the equation.) The R-value is the sum
of the ``Slab/PerimeterInsulation/Layer/NominalRValue`` element values for each
foundation wall. For each slab, an effective R-value is looked up based on the
nearest R-value in the following table.

.. table:: Slab insulation effective R-values

   =================  ==================
   Insulation Level   Effective R-value   
   =================  ==================
   R-0                4                   
   R-5                7.9                 
   =================  ==================

Then a weighted average R-value is calculated by weighting the U-values by area.

.. math::
   :nowrap:

   \begin{align*}
   U_i &= \frac{1}{R_i} \\
   U_{eff,avg} &= \frac{\sum_i{U_i A_i}}{\sum_i A_i} \\
   R_{eff,avg} &= \frac{1}{U_{eff,avg}} \\
   \end{align*}

The effective R-value of the R-0 insulation level is then subtracted.

.. math::

   R = R_{eff,avg} - 4.0
   
Finally, the nearest insulation level is selected from the enumeration list.

.. _floor-insulation:

Floor insulation above basement or crawlspace
*********************************************

If the foundation type is a basement or crawlspace, for each frame floor above
the foundation, a weighted average using the floor area and R-value are
calculated. The area is obtained from the ``Area`` element.

The floor R-value can be described by using ``NominalRValue`` or ``AssemblyRValue``.
If a user wishes to use a nominal R-value, ``NominalRValue`` elements for all layers need to be provided.
Otherwise, ``AssemblyRValue`` elements for each layer need to be provided.

If nominal R-value is used, the R-value is the sum of the ``FrameFloor/Insulation/Layer/NominalRValue`` element values 
for each frame floor. The nearest discrete R-value from the list of possible R-values for that floor type
is used to determine an assembly code. 
Then, the assembly R-value of the corresponding assembly code from the lookup table is used. 
The lookup table can be found at `hescorehpxml\\lookups\\lu_floor_eff_rvalue.csv
<https://github.com/NREL/hescore-hpxml/blob/master/hescorehpxml/lookups/lu_floor_eff_rvalue.csv>`_.

If assembly R-value is used, the discrete R-value nearest to assembly R-value
from the lookup table is used. The lookup table can be found at `hescorehpxml\\lookups\\lu_floor_eff_rvalue.csv
<https://github.com/NREL/hescore-hpxml/blob/master/hescorehpxml/lookups/lu_floor_eff_rvalue.csv>`_.

When more than one HPXML ``FrameFloor`` element must be combined into one floor
construction for HEScore, a weighted average assembly R-value is determined by weighting the U-values by area.

.. math::
   :nowrap:

   \begin{align*}
   U_i &= \frac{1}{R_i} \\
   U_{eff,avg} &= \frac{\sum_i{U_i A_i}}{\sum_i A_i} \\
   R_{eff,avg} &= \frac{1}{U_{eff,avg}} \\
   \end{align*}

Then the discrete R-value nearest to the weighted average assembly R-value from the lookup table is used.

