# Copyright (c) 2014-2015, NVIDIA CORPORATION.  All rights reserved.

import tempfile
import StringIO

from nose.tools import assert_raises
import mock
import PIL.Image
import numpy as np

from . import image as _

class TestLoadImage():

    def test_bad_path(self):
        """load_image with bad path"""
        for path in [
                'some string',
                '/tmp/not-a-file',
                'http://not-a-url',
                ]:
            yield self.check_none, path

    def check_none(self, path):
        assert _.load_image(path) is None

    @mock.patch('digits.utils.image.PIL.Image')
    @mock.patch('digits.utils.image.os.path')
    def test_good_file(self, mock_path, mock_Image):
        """load_image with good file"""
        mock_path.exists.return_value = True
        mock_Image.open = mock.Mock()
        assert _.load_image('/a/file') is not None
        mock_Image.open.assert_called_with('/a/file')

    @mock.patch('digits.utils.image.PIL.Image')
    @mock.patch('digits.utils.image.cStringIO')
    @mock.patch('digits.utils.image.requests')
    def test_good_url(self, mock_requests, mock_cStringIO, mock_Image):
        """load_image with good url"""
        # requests
        response = mock.Mock()
        response.status_code = mock_requests.codes.ok
        response.content = 'some content'
        mock_requests.get.return_value = response

        # cStringIO
        mock_cStringIO.StringIO = mock.Mock()
        mock_cStringIO.StringIO.return_value = 'an object'

        # Image
        mock_Image.open = mock.Mock()

        assert _.load_image('http://some-url') is not None
        mock_cStringIO.StringIO.assert_called_with('some content')
        mock_Image.open.assert_called_with('an object')

    def test_corrupted_file(self):
        """load_image with corrupted file"""
        image = PIL.Image.fromarray(np.zeros((10,10,3),dtype=np.uint8))

        # Save image to a JPEG buffer.
        buffer_io = StringIO.StringIO()
        image.save(buffer_io, format='jpeg')
        encoded = buffer_io.getvalue()
        buffer_io.close()

        # Corrupt the second half of the image buffer.
        size = len(encoded)
        corrupted = encoded[:size/2] + encoded[size/2:][::-1]

        # Save the corrupted image to a temporary file.
        f = tempfile.NamedTemporaryFile(delete=False)
        f.write(corrupted)
        f.close()

        assert _.load_image(f.name) is None

class TestResizeImage():

    @classmethod
    def setup_class(cls):
        cls.np_gray = np.random.randint(0, 255, (10,10)).astype('uint8')
        cls.pil_gray = PIL.Image.fromarray(cls.np_gray)
        cls.np_color = np.random.randint(0, 255, (10,10,3)).astype('uint8')
        cls.pil_color = PIL.Image.fromarray(cls.np_color)

    def test_configs(self):
        """resize_image"""
        # lots of configs tested here
        for h in [10, 15]:
            for w in [10, 16]:
                for t in ['gray', 'color']:
                    # test channels=None (should autodetect channels)
                    if t == 'color':
                        s = (h, w, 3)
                    else:
                        s = (h, w)
                    yield self.verify_pil, (h, w, None, None, t, s)
                    yield self.verify_np, (h, w, None, None, t, s)

                    # test channels={3,1}
                    for c in [3, 1]:
                        for m in ['squash', 'crop', 'fill', 'half_crop']:
                            if c == 3:
                                s = (h, w, 3)
                            else:
                                s = (h, w)
                            yield self.verify_pil, (h, w, c, m, t, s)
                            yield self.verify_np, (h, w, c, m, t, s)

    def verify_pil(self, args):
        """pass a PIL.Image to resize_image and check the returned dimensions"""
        h, w, c, m, t, s = args
        if t == 'gray':
            i = self.pil_gray
        else:
            i = self.pil_color
        r = _.resize_image(i, h, w, c, m)
        assert r.shape == s, 'Resized PIL.Image (orig=%s) should have been %s, but was %s %s' % (i.size, s, r.shape, self.args_to_str(args))
        assert r.dtype == np.uint8, 'image.dtype should be uint8, not %s' % r.dtype

    def verify_np(self, args):
        """pass a numpy.ndarray to resize_image and check the returned dimensions"""
        h, w, c, m, t, s = args
        if t == 'gray':
            i = self.np_gray
        else:
            i = self.np_color
        r = _.resize_image(i, h, w, c, m)
        assert r.shape == s, 'Resized np.ndarray (orig=%s) should have been %s, but was %s %s' % (i.shape, s, r.shape, self.args_to_str(args))
        assert r.dtype == np.uint8, 'image.dtype should be uint8, not %s' % r.dtype

    def args_to_str(self, args):
        return """
        height=%s
        width=%s
        channels=%s
        resize_mode=%s
        image_type=%s
        shape=%s""" % args


