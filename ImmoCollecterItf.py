
import abc
class ImmoCollecterItf(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def get_list_all_houses():
        raise NotImplementedError
    
    @abc.abstractmethod
    def get_house_details(house_ref):
        raise NotImplementedError