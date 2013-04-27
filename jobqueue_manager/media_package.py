
class MediaPackage():
    """
    Abstract MediaPackage class
    """
    pass

class MoviePackage(MediaPackage):
    """
    Package for a Movie
    """
    pass

class TVBasePackage(MediaPackage):
    """
    Package for a TV base folder (no seasons)
    """
    pass

class TVSeasonPackage(TVPackage):
    """
    Package for a certain TV Season
    """
    pass

class MediaPackageManager():
    """
    Provides an API to the MediaPackages
    """
    pass
