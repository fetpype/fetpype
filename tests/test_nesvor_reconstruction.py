import unittest
from unittest.mock import MagicMock, patch
from fetpype.nodes.nesvor import (
    NesvorReconstructionInputSpec,
    NesvorReconstructionOutputSpec,
    NesvorReconstruction,
)
import os


class TestNesvorReconstructionInputSpec(unittest.TestCase):
    """
    Unit test for NesvorReconstructionInputSpec class.
    """

    def setUp(self) -> None:
        """
        Set up testing environment.
        """
        self.nesvor_reconstruction_input_spec = NesvorReconstructionInputSpec()

    def test_attributes(self) -> None:
        """
        Test whether NesvorReconstructionInputSpec class has necessary
        attributes.
        """
        self.assertTrue(
            hasattr(self.nesvor_reconstruction_input_spec, "input_slices")
        )
        self.assertTrue(
            hasattr(self.nesvor_reconstruction_input_spec, "output_volume")
        )


class TestNesvorReconstructionOutputSpec(unittest.TestCase):
    """
    Unit test for NesvorReconstructionOutputSpec class.
    """

    def setUp(self) -> None:
        """
        Set up testing environment.
        """
        self.nesvor_reconstruction_output_spec = (
            NesvorReconstructionOutputSpec()
        )

    def test_attributes(self) -> None:
        """
        Test whether NesvorReconstructionOutputSpec class has necessary
        attributes.
        """
        self.assertTrue(
            hasattr(self.nesvor_reconstruction_output_spec, "output_volume")
        )


class TestNesvorReconstruction(unittest.TestCase):
    """
    Unit test for NesvorReconstruction class.
    """

    def setUp(self) -> None:
        """
        Set up testing environment.
        """
        self.nesvor_reconstruction = NesvorReconstruction()

    def test_attributes(self) -> None:
        """
        Test whether NesvorReconstruction class has necessary attributes.
        """
        self.assertTrue(hasattr(self.nesvor_reconstruction, "_cmd"))
        self.assertTrue(hasattr(self.nesvor_reconstruction, "input_spec"))
        self.assertTrue(hasattr(self.nesvor_reconstruction, "output_spec"))

    @patch.object(os, "makedirs")
    @patch.object(os.path, "dirname")
    def test_gen_filename(self, mock_dirname, mock_makedirs) -> None:
        """
        Test _gen_filename method.
        """
        mock_dirname.return_value = "/some/fake/path"
        self.nesvor_reconstruction.inputs.output_volume = MagicMock()
        self.nesvor_reconstruction.inputs.input_slices = MagicMock()
        self.assertEqual(
            self.nesvor_reconstruction._gen_filename("output_volume"),
            "/some/fake/path/recon/recon.nii.gz",
        )


if __name__ == "__main__":
    unittest.main()
