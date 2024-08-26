from rocmi import kfd

from pyfakefs.fake_filesystem_unittest import TestCase


class KFDTestCase(TestCase):
    def setUp(self):
        self.setUpPyfakefs()

    def test_get_processes_no_allocs(self):
        """Verify get_processes works with a PID without any GPU memory reserved."""

        self.fs.create_file("/proc/4444/comm", contents=b"test-process")
        self.fs.create_file("/sys/class/kfd/kfd/proc/4444/pasid", contents=b"1234")
        self.fs.create_dir("/sys/class/kfd/kfd/proc/4444/queues")

        for p in kfd.get_processes():
            self.assertEqual(p.name, "test-process")
            self.assertEqual(p.pasid, 1234)
