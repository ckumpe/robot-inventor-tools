
import unittest
import gateway
import tempfile


class NoopLoggerTestCase(unittest.TestCase):
    def setUp(self):
        self.log = gateway.NoopLogger()

    def test_input(self):
        # just ensure method can be called silently
        self.log.input("an input line")

    def test_output(self):
        # just ensure method can be called silently
        self.log.output("an output line")

class FileLoggerTestCase(unittest.TestCase):
    def setUp(self):
        self.file = tempfile.NamedTemporaryFile(delete=True)
        self.log = gateway.FileLogger(self.file.name)

    def test_input(self):
        self.log.input(b"an input line")        

        line = self.file.read(1024)
        self.assertEqual(line, b"< an input line\n")

    def test_output(self):
        self.log.output(b"an output line")        

        line = self.file.read(1024)
        self.assertEqual(line, b"> an output line\n")


if __name__ == '__main__':
    unittest.main()
