import unittest
from traits.api import List as TraitsList, Either, Bool
from unittest.mock import patch
from fetpype.nodes.nesvor import (
    NesvorSegmentationInputSpec,
    NesvorSegmentationOutputSpec,
    NesvorSegmentation,
)


class TestNesvorSegmentationInputSpec(unittest.TestCase):
    """
    Unit test for NesvorSegmentationInputSpec class.
    """

    def setUp(self) -> None:
        """
        Set up testing environment.
        """
        self.input_spec = NesvorSegmentationInputSpec()

    def test_attributes(self) -> None:
        """
        Test whether NesvorSegmentationInputSpec class has
        necessary attributes.
        """
        self.assertTrue(hasattr(self.input_spec, "input_stacks"))
        self.assertTrue(hasattr(self.input_spec, "output_stack_masks"))
        self.assertTrue(hasattr(self.input_spec, "no_augmentation_seg"))
        self.assertTrue(hasattr(self.input_spec, "pre_command"))
        self.assertTrue(hasattr(self.input_spec, "nesvor_image"))

    def test_input_stacks_type(self) -> None:
        """
        Test the type of input_stacks attribute.
        """
        self.assertIsInstance(self.input_spec.input_stacks, TraitsList)

    def test_output_stack_masks_type(self) -> None:
        """
        Test the type of output_stack_masks attribute.
        """
        self.assertIsInstance(self.input_spec.output_stack_masks, Either)

    def test_no_augmentation_seg_type(self) -> None:
        """
        Test the type of no_augmentation_seg attribute.
        """
        self.assertIsInstance(self.input_spec.no_augmentation_seg, Bool)

    def test_no_augmentation_seg_value(self) -> None:
        """
        Test the default value of no_augmentation_seg attribute.
        """
        self.assertFalse(self.input_spec.no_augmentation_seg)

    def test_pre_command_type(self) -> None:
        """
        Test the type of pre_command attribute.
        """
        self.assertIsInstance(self.input_spec.pre_command, str)

    def test_nesvor_image_type(self) -> None:
        """
        Test the type of nesvor_image attribute.
        """
        self.assertIsInstance(self.input_spec.nesvor_image, str)


class TestNesvorSegmentationOutputSpec(unittest.TestCase):
    """
    Unit test for NesvorSegmentationOutputSpec class.
    """

    def setUp(self) -> None:
        """
        Set up testing environment.
        """
        self.output_spec = NesvorSegmentationOutputSpec()

    def test_attributes(self) -> None:
        """
        Test whether NesvorSegmentationOutputSpec class has necessary
        attributes.
        """
        self.assertTrue(hasattr(self.output_spec, "output_stack_masks"))

    def test_output_stack_masks_type(self) -> None:
        """
        Test the type of output_stack_masks attribute.
        """
        self.assertIsInstance(self.output_spec.output_stack_masks, TraitsList)


class TestNesvorSegmentation(unittest.TestCase):
    def setUp(self):
        """
        Method to set up necessary parameters for tests.
        """
        self.inputs = {
            "pre_command": "test",
            "nesvor_image": "test_image",
            "input_stacks": ["stack1.nii.gz", "stack2.nii.gz"],
        }

    def test_init(self):
        """
        Test the __init__ function to ensure it is initializing as expected.
        """
        nesvor_seg = NesvorSegmentation(**self.inputs)
        expected_cmd = (
            f"{self.inputs['pre_command']} "
            f"{self.inputs['nesvor_image']} "
            "nesvor segment-stack"
        )
        self.assertEqual(nesvor_seg._cmd, expected_cmd)

    @patch("os.getcwd", return_value="/path/to/cwd")
    def test_gen_filename(self, mock_getcwd):
        """
        Test the _gen_filename function to ensure it is generating
        filenames as expected.
        """
        nesvor_seg = NesvorSegmentation(**self.inputs)
        expected_output = [
            "/path/to/cwd/stack1_mask.nii.gz",
            "/path/to/cwd/stack2_mask.nii.gz",
        ]
        self.assertEqual(
            nesvor_seg._gen_filename("output_stack_masks"), expected_output
        )

    def test_list_outputs(self):
        """
        Test the _list_outputs function to ensure it is listing outputs
        as expected.
        """
        nesvor_seg = NesvorSegmentation(**self.inputs)
        nesvor_seg.inputs.output_stack_masks = [
            "/path/to/output/stack1_mask.nii.gz",
            "/path/to/output/stack2_mask.nii.gz",
        ]
        expected_outputs = {
            "output_stack_masks": [
                "/path/to/output/stack1_mask.nii.gz",
                "/path/to/output/stack2_mask.nii.gz",
            ]
        }
        self.assertDictEqual(nesvor_seg._list_outputs(), expected_outputs)

    def test_format_arg(self):
        """
        Test the _format_arg function to ensure it is formatting arguments
        as expected.
        """
        nesvor_seg = NesvorSegmentation(**self.inputs)
        self.assertEqual(
            nesvor_seg._format_arg("pre_command", None, "test"), ""
        )
        self.assertEqual(
            nesvor_seg._format_arg("nesvor_image", None, "test_image"), ""
        )
        self.assertEqual(
            nesvor_seg._format_arg("other_arg", None, "test_other"),
            "other_arg test_other",
        )


if __name__ == "__main__":
    unittest.main()
