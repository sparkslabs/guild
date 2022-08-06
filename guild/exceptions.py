class UnboundActorMethod(Exception): #NOTE: Overview documented
    pass


class ActorNotStartedException(Exception): #NOTE: Overview documented
    pass


class ActorException(Exception):   #NOTE: Overview documented
    def __init__(self, *argv, **argd):
        super(ActorException, self).__init__(*argv)
        self.__dict__.update(argd)

class JobCancelled(Exception):
    pass
