import logging

def setupLogger() -> logging.Logger:
    """
    Set up a logger with a specific format and file handler.
    
    Returns:
        logging.Logger: Configured logger object.
    """
    logger = logging.getLogger('server')
    logger.setLevel(logging.INFO)
    
    # Create file handler which logs even debug messages
    fH = logging.FileHandler('server.log')
    fH.setLevel(logging.INFO)
    
    # Create console handler with a higher log level
    cH = logging.StreamHandler()
    cH.setLevel(logging.ERROR)
    
    # Create formatter and add it to the handlers
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
    fH.setFormatter(formatter)
    cH.setFormatter(formatter)
    
    # Add the handlers to the logger
    logger.addHandler(fH)
    logger.addHandler(cH)
    
    return logger
