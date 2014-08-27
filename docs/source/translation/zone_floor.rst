Foundation Insulation
#####################

.. contents:: Table of Contents

Determining the primary foundation
**********************************

The foundation that covers the largest square footage is selected as the primary
foundation. This is determined by summing up the area of the ``FrameFloor`` or
``Slab`` elements (depending on what kind of foundation it is).

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
   |Garage                                    |*not translated*         |
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

If the foundation type is a basement or crawlspace, for each foundation wall a
*UA* is calculated with the wall area and R-value. The area is obtained from
the ``Area`` element, if present, or calculated from the ``Length`` and
``Height`` elements. The R-value is the sum of the
``FoundationWall/Insulation/Layer/NominalRValue`` element values for each
foundation wall. Then an equivalent R-value is calculated using the method
described in :ref:`roof-rvalues`.

If the foundation type is a slab on grade, for each foundation wall a *UA* is
calculated using the value of ``ExposedPerimeter`` as the area. (The units work
out, the depth in the area drops out of the equation.) The R-value is the sum
of the ``Slab/PerimeterInsulation/Layer/NominalRValue`` element values for each
foundation wall. Then an equivalent R-value is calculated, also using the
method described in :ref:`roof-rvalues`.

Floor insulation above basement or crawlspace
*********************************************

If the foundation type is a basement or crawlspace, for each frame floor above
the foundation a *UA* is calculated from the floor area and R-value. The area
is obtained from the ``Area`` element. The R-value is the sum of the
``FrameFloor/Insulation/Layer/NominalRValue`` element values for each
foundation wall. Then an equivalent R-value is calculated using the method
described in :ref:`roof-rvalues`. Finally, the floor assembly code with the nearest
R-value is selected. 



