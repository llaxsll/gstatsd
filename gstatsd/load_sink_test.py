import datetime
import unittest

from load_sink import StatAggregate
class TestStatAggregates(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_stat_all_frames(self):
        stats = StatAggregate()
            
        for i in range(1,21):
            stats._move_frame_forward()
            stats.stat('All', client_requests = 1)
            stats.stat('All', avg_count = (i + 0.5,'avg'))
        
        stat_frame = stats.collect(50)
        
        self.assertEquals(stat_frame['All']['client_requests'], 15)
        self.assertEquals(stat_frame['All']['avg_count'], 13.5)
        
    def test_stat_two_frame(self):
        stats = StatAggregate()
        stats.stat('Twinkie', client_requests = 1)
        stats.stat('Twinkie', client_requests = 1)
        
        stats.stat('Twinkie', max_response_time = (1,'max'))
        stats.stat('Twinkie', max_response_time = (5,'max'))

        stats.stat('Twinkie', avg_response_time = (1,'avg'))
        stats.stat('Twinkie', avg_response_time = (5,'avg'))

        stats._move_frame_forward()
        
        stats.stat('Twinkie', client_requests = 1)
        stats.stat('Twinkie', client_requests = 1)
        
        stats.stat('Twinkie', max_response_time = (3,'max'))
        stats.stat('Twinkie', max_response_time = (4,'max'))

        stats.stat('Twinkie', avg_response_time = (4,'avg'))
        stats.stat('Twinkie', avg_response_time = (4,'avg'))
        
        last_frame_stats = stats.collect(1)
        two_frame_stats = stats.collect(2)
        
        self.assertEquals(last_frame_stats['Twinkie']['client_requests'], 2)
        self.assertEquals(two_frame_stats['Twinkie']['client_requests'], 4)
        
        self.assertEquals(last_frame_stats['Twinkie']['max_response_time'], 4)
        self.assertEquals(two_frame_stats['Twinkie']['max_response_time'], 5)
        
        self.assertEquals(last_frame_stats['Twinkie']['avg_response_time'], 4)
        self.assertEquals(two_frame_stats['Twinkie']['avg_response_time'], 3.5)
        
    def test_stat_one_frame(self):
        stats = StatAggregate()
        
        stats.stat('Twinkie', client_requests = 1)
        stats.stat('Twinkie', client_requests = 1)
        
        stats.stat('Twinkie', max_response_time = (300,'max'))
        stats.stat('Twinkie', max_response_time = (350,'max'))

        stats.stat('Twinkie', avg_response_time = (300,'avg'))
        stats.stat('Twinkie', avg_response_time = (350,'avg'))
        
        
        stats.stat('Twinkie', response = '200')
        stats.stat('Twinkie', response = '200')
        stats.stat('Twinkie', response = '500')
        stats.stat('Twinkie', response = '200')
        
        stat_frame = stats.collect(1)

        self.assertEquals(stat_frame['Twinkie']['client_requests'], 2)
        self.assertEquals(stat_frame['Twinkie']['max_response_time'], 350)
        self.assertEquals(stat_frame['Twinkie']['avg_response_time'], 325)
        self.assertEquals(stat_frame['Twinkie']['response']['200'], 3 )
        self.assertEquals(stat_frame['Twinkie']['response']['500'], 1 )
        
