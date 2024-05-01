import logging
import cv2
from PIL import Image
import numpy as np
from utils import stream_tools as st
from skimage.metrics import structural_similarity as ssim
from typing import Tuple, List, Union
params = st.params


def display_image(img1: Image, pfp_link: str) -> None:
    """
    Display the PIL.Image using openCV
    """
    img1_cv = np.array(img1)
    img1_cv = cv2.cvtColor(img1_cv, cv2.COLOR_BGR2RGB)
    img1_cv = cv2.resize(img1_cv, (500, 500))
    cv2.imshow(f"PFP Image {pfp_link}", img1_cv)
    cv2.waitKey(1)


def check_pfp(pfp: Image, 
              compare_image: np.ndarray, 
              folder_path: str, 
              filename: str, 
              threshold: float) -> Tuple[bool, List[str] | str]:
    """
    Using skimage structural similarity and compare against 5-7 images to determine if in collection or not

    TODO: update this to use image proc ML model instead of heuristics comparison

    :param pfp: the Image to compare
    :parm compare_image: the image to compare against
    :param folder_path: the folder with images to compare against
    :param filename: file name to compare against
    :param threshold: the acceptable threshold for similarity

    return: boolean if true and list of matching ids found
    """
    matched_ids, missing_ids = [], []
    twinsies, likely_pfps, likely_matches = [], [], []

    sims, lowest_sim, highest_sim, average_sim = [], 100, 0, 0
    logging.info("Displaying image...")

    sim = ssim(np.array(pfp), compare_image, multichannel=True)
    logging.info(f"SSIM: {sim}")
    sims.append(sim)
    average_sim = sum(sims)/len(sims)
    lowest_sim = min(sims)
    highest_sim = max(sims)
    logging.debug(f"\nLowest SSIM: {lowest_sim}\n Highest SSIM: {highest_sim}\nAverage SSIM: {average_sim}\n")
    if sim > 0.925:
        logging.info(f"\nMatched: {pfp} -> {filename}")
        if folder_path+"/"+filename not in matched_ids:
            matched_ids.append(
                folder_path+"/"+filename)
            cv2.destroyAllWindows()
        return True, matched_ids
    if sim > 0.9:
        logging.info(f"\nTwinsies: {pfp} -> {filename}")
        if folder_path+"/"+filename not in twinsies:
            twinsies.append(folder_path+"/"+filename)
            cv2.destroyAllWindows()
        return True, twinsies
    if sim > threshold:
        logging.info(f"\nLikely Match: {pfp} -> {filename}")
        if folder_path+"/"+filename not in likely_matches:
            likely_pfps.append(pfp)
            likely_matches.append(
                folder_path+"/"+filename)
            cv2.destroyAllWindows()
        return True, likely_pfps
    if sim < threshold and folder_path+"/"+filename not in missing_ids:
        missing_ids.append(folder_path+"/"+filename)
        cv2.destroyAllWindows()
        return False, "No match found"
    else:
        return False, "No match found"