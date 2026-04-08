# """Samples routes package."""
from tuned.apis.main.routes.content.levels import GetAcademicLevels
from tuned.apis.main.routes.content.samples import SampleListView, SampleDetailView, SampleServiceView, SampleRelatedView
from tuned.apis.main.routes.content.tags import GetTagsList

__all__ = ['GetAcademicLevels', 'SampleListView', 'SampleDetailView', 'SampleServiceView', 'SampleRelatedView', 'GetTagsList']
