import pathlib
from unittest.mock import patch

from auto_labeling_pipeline.mappings import AmazonComprehendSentimentTemplate
from auto_labeling_pipeline.models import RequestModelFactory
from rest_framework import status
from rest_framework.reverse import reverse

from ...models import DOCUMENT_CLASSIFICATION
from ...views.auto_labeling import load_data_as_b64
from .utils import CRUDMixin, prepare_project

data_dir = pathlib.Path(__file__).parent / 'data'


class TestConfigParameter(CRUDMixin):

    def setUp(self):
        self.project = prepare_project(task=DOCUMENT_CLASSIFICATION)
        self.data = {
            'model_name': 'GCP Entity Analysis',
            'model_attrs': {'key': 'hoge', 'type': 'PLAIN_TEXT', 'language': 'en'},
            'text': 'example'
        }
        self.url = reverse(viewname='auto_labeling_parameter_testing', args=[self.project.item.id])

    @patch('api.views.auto_labeling.AutoLabelingConfigParameterTest.send_request', return_value={})
    def test_called_with_proper_model(self, mock):
        self.assert_create(self.project.users[0], status.HTTP_200_OK)
        _, kwargs = mock.call_args
        expected = RequestModelFactory.create(self.data['model_name'], self.data['model_attrs'])
        self.assertEqual(kwargs['model'], expected)

    @patch('api.views.auto_labeling.AutoLabelingConfigParameterTest.send_request', return_value={})
    def test_called_with_text(self, mock):
        self.assert_create(self.project.users[0], status.HTTP_200_OK)
        _, kwargs = mock.call_args
        self.assertEqual(kwargs['example'], self.data['text'])

    @patch('api.views.auto_labeling.AutoLabelingConfigParameterTest.send_request', return_value={})
    def test_called_with_image(self, mock):
        self.data['text'] = load_data_as_b64(data_dir / 'images/1500x500.jpeg')
        self.assert_create(self.project.users[0], status.HTTP_200_OK)
        _, kwargs = mock.call_args
        self.assertEqual(kwargs['example'], self.data['text'])


class TestTemplateMapping(CRUDMixin):

    def setUp(self):
        self.project = prepare_project(task=DOCUMENT_CLASSIFICATION)
        self.data = {
            'response': {
                'Sentiment': 'NEUTRAL',
                'SentimentScore': {
                    'Positive': 0.004438233096152544,
                    'Negative': 0.0005306027014739811,
                    'Neutral': 0.9950305223464966,
                    'Mixed': 5.80838445785048e-7
                }
            },
            'template': AmazonComprehendSentimentTemplate().load()
        }
        self.url = reverse(viewname='auto_labeling_template_test', args=[self.project.item.id])

    def test_template_mapping(self):
        response = self.assert_create(self.project.users[0], status.HTTP_200_OK)
        expected = [{'label': 'NEUTRAL'}]
        self.assertEqual(response.json(), expected)

    def test_json_decode_error(self):
        self.data['template'] = ''
        self.assert_create(self.project.users[0], status.HTTP_400_BAD_REQUEST)


class TestLabelMapping(CRUDMixin):

    def setUp(self):
        self.project = prepare_project(task=DOCUMENT_CLASSIFICATION)
        self.data = {
            'response': [{'label': 'NEGATIVE'}],
            'label_mapping': {'NEGATIVE': 'Negative'}
        }
        self.url = reverse(viewname='auto_labeling_mapping_test', args=[self.project.item.id])

    def test_label_mapping(self):
        response = self.assert_create(self.project.users[0], status.HTTP_200_OK)
        expected = [{'label': 'Negative'}]
        self.assertEqual(response.json(), expected)
