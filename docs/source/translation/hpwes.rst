Home Performance with Energy Star
#################################

Inputs for the Home Energy Score `submit_hpwes`_ API call can now be retrieved
from an HPXML file.

Project
*******

To get the Home Performance with Energy Star (HPwES) data
from an HPXML file a ``Project`` node needs to be included with at least the
following elements:

.. _submit_hpwes: https://hes-documentation.labworks.org/home/api-definitions/api-methods/submit_hpwes

.. code:: xml

    <Project>
        <ProjectDetails>
            <ProjectSystemIdentifiers id="projectid"/>
            <ProgramCertificate>Home Performance with Energy Star</ProgramCertificate>
            <StartDate>2018-08-20</StartDate>
            <CompleteDateActual>2018-12-14</CompleteDateActual>
        </projectDetails>
    </Project>

If more than one ``Project`` element exists, the first one will be used. The
user can override this by passing the ``--projectid`` argument to the translator
command line. To translate the HPwES fields, the ``ProgramCertificate`` must be
present and equal to ``Home Performance with Energy Star``.

The project fields are mapped as follows:

+---------------------------------------+----------------------------------------------+
|       HPXML ``ProjectDetails``        |          `submit_hpwes`_ API value           |
+=======================================+==============================================+
| ``StartDate``                         | ``improvement_installation_start_date``      |
+---------------------------------------+----------------------------------------------+
| ``CompleteDateActual``                | ``improvement_installation_completion_date`` |
+---------------------------------------+----------------------------------------------+

Contractor
**********

A ``Contractor`` element is also required with at minimum the following
elements:

.. code:: xml

    <Contractor>
        <ContractorDetails>
            <SystemIdentifier id="contractor1"/>
            <BusinessInfo>
                <SystemIdentifier id="contractor1businessinfo"/>
                <BusinessName>My HPwES Contractor Business</BusinessName>
                <extension>
                    <ZipCode>12345</ZipCode>
                </extension>
            </BusinessInfo>
        </ContractorDetails>
    </Contractor>

If there are more than one ``Contractor`` elements, the contractor with the id
passed in the ``--contractorid`` command line argument is used. If no contracter
id is specified by the user, the contractor listed in the
``Building/ContractorID`` will be used. If that element isn't available, the
first ``Contractor`` element will be used.

The contractor fields are mapped as follows:

+------------------------------------------------------+------------------------------+
|                 HPXML ``Contractor``                 |  `submit_hpwes`_ API value   |
+======================================================+==============================+
| ``ContractorDetails/BusinessInfo/BusinessName``      | ``contractor_business_name`` |
+------------------------------------------------------+------------------------------+
| ``ContractorDetails/BusinessInfo/extension/ZipCode`` | ``contractor_zip_code``      |
+------------------------------------------------------+------------------------------+
