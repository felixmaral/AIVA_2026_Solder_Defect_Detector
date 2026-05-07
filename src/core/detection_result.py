from typing import List
from .solder_defect import SolderDefect


class DetectionResult:
    """
    Aggregates all defects found during a single PCB inspection cycle.

    This class acts as the output contract between the ``Detector`` inference
    engine and the rest of the system. It collects the individual ``SolderDefect``
    instances produced during a run and provides bulk serialisation to XML, which
    is the primary data exchange format with the robot control software.

    Attributes:
        defects (List[SolderDefect]): Ordered list of all detected defects.
            Empty if the inspection found no anomalies.
    """

    def __init__(self):
        """
        Initialises an empty defect registry for a new inspection cycle.
        """
        self.defects: List[SolderDefect] = []

    def add_defect(self, defect: SolderDefect) -> None:
        """
        Registers a newly discovered defect into the result registry.

        Args:
            defect (SolderDefect): The defect instance to register, as produced
                by the inference engine for a single detected bounding box.
        """
        self.defects.append(defect)

    def to_xml(self) -> str:
        """
        Serialises the complete defect registry into a well-formed XML manifest.

        The root ``<result>`` element contains a ``<detection_count>`` summary
        field followed by one ``<defect>`` block per detected anomaly. The
        manifest is terminated with a trailing newline for compatibility with
        standard file writing conventions.

        Returns:
            str: A complete, well-formed XML string representing the full
                 inspection result, including all detected defects.

        Example::

            <result>
                <detection_count>2</detection_count>
                <defect>
                    <x>120</x>
                    ...
                </defect>
            </result>
        """
        # Build the manifest header with the global detection count summary
        lines = [
            "<result>",
            f"    <detection_count>{len(self.defects)}</detection_count>",
        ]

        # Append the XML fragment of each individual detected bounding box
        for defect in self.defects:
            lines.append(defect.to_xml_string())

        lines.append("</result>")

        # Join all fragments and append the trailing carriage return
        return "\n".join(lines) + "\n"