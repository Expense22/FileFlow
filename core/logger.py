import logging

def setup_logger(log_file="fileflow.log"):
    logger = logging.getLogger("FileFlow")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        # Запись в файл
        handler = logging.FileHandler(log_file, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Вывод в консоль
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        logger.addHandler(console)
        
    return logger