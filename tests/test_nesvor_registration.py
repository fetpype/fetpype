import unittest
from traits.api import List as TraitsList, File
from fetpype.nodes.nesvor import (
    NesvorRegisterOutputSpec,
    NesvorRegisterInputSpec,
    NesvorRegistration,
)
from unittest.mock import patch


class TestNesvorRegisterOutputSpec(unittest.TestCase):
    """
    Unit test for NesvorRegisterOutputSpec class.
    """

    def setUp(self) -> None:
        """
        Set up testing environment.
        """
        self.output_spec = NesvorRegisterOutputSpec()

    def test_attributes(self) -> None:
        """
        Test whether NesvorRegisterOutputSpec class has necessary attributes.
        """
        self.assertTrue(hasattr(self.output_spec, "output_slices"))

    def test_output_slices_type(self) -> None:
        """
        Test the type of output_slices attribute.
        """
        self.assertIsInstance(self.output_spec.output_slices, File)


class TestNesvorRegisterInputSpec(unittest.TestCase):
    """
    Unit test for NesvorRegisterInputSpec class.
    """

    def setUp(self) -> None:
        """
        Set up testing environment.
        """
        self.input_spec = NesvorRegisterInputSpec()

    def test_attributes(self) -> None:
        """
        Test whether NesvorRegisterInputSpec class has necessary attributes.
        """
        self.assertTrue(hasattr(self.input_spec, "input_stacks"))
        self.assertTrue(hasattr(self.input_spec, "stack_masks"))
        self.assertTrue(hasattr(self.input_spec, "output_slices"))
        self.assertTrue(hasattr(self.input_spec, "output_json"))
        self.assertTrue(hasattr(self.input_spec, "output_log"))

    def test_input_stacks_type(self) -> None:
        """
        Test the type of input_stacks attribute.
        """
        self.assertIsInstance(self.input_spec.input_stacks, TraitsList)

    def test_stack_masks_type(self) -> None:
        """
        Test the type of stack_masks attribute.
        """
        self.assertIsInstance(self.input_spec.stack_masks, TraitsList)

    def test_output_slices_type(self) -> None:
        """
        Test the type of output_slices attribute.
        """
        self.assertIsInstance(self.input_spec.output_slices, File)

    def test_output_json_type(self) -> None:
        """
        Test the type of output_json attribute.
        """
        self.assertIsInstance(self.input_spec.output_json, File)

    def test_output_log_type(self) -> None:
        """
        Test the type of output_log attribute.
        """
        self.assertIsInstance(self.input_spec.output_log, File)


class TestNesvorRegistration(unittest.TestCase):
    def setUp(self):
        """
        Method to set up necessary parameters for tests.
        """
        self.inputs = {"pre_command": "test", "nesvor_image": "test_image"}

    def test_init(self):
        """
        Test the __init__ function to ensure it is initializing as expected.
        """
        nesvor_reg = NesvorRegistration(**self.inputs)
        expected_cmd = (
            f"{self.inputs['pre_command']} "
            "{self.inputs['nesvor_image']} "
            "nesvor register"
        )
        self.assertEqual(nesvor_reg._cmd, expected_cmd)

    @patch("os.getcwd", return_value="/path/to/cwd")
    def test_gen_filename(self, mock_getcwd):
        """
        Test the _gen_filename function to ensure it is generating filenames
         as expected.
        """
        nesvor_reg = NesvorRegistration(**self.inputs)
        expected_output = "/path/to/cwd/slices"
        self.assertEqual(
            nesvor_reg._gen_filename("output_slices"), expected_output
        )

    def test_list_outputs(self):
        """
        Test the _list_outputs function to ensure it is listing outputs
         as expected.
        """
        nesvor_reg = NesvorRegistration(**self.inputs)
        nesvor_reg.inputs.output_slices = "/path/to/output_slices"
        expected_outputs = {"output_slices": "/path/to/output_slices"}
        self.assertDictEqual(nesvor_reg._list_outputs(), expected_outputs)

    def test_format_arg(self):
        """
        Test the _format_arg function to ensure it is formatting arguments
         as expected.
        """
        nesvor_reg = NesvorRegistration(**self.inputs)
        self.assertEqual(
            nesvor_reg._format_arg("pre_command", None, "test"), ""
        )
        self.assertEqual(
            nesvor_reg._format_arg("nesvor_image", None, "test_image"), ""
        )
        self.assertEqual(
            nesvor_reg._format_arg("other_arg", None, "test_other"),
            "other_arg test_other",
        )


if __name__ == "__main__":
    unittest.main()
