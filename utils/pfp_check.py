# import pandas as pd
# import os
import requests
import cv2
from PIL import Image
import numpy as np
# from io import BytesIO
from utils import stream_tools as st
from utils import postgres_tools as pg
from skimage.metrics import structural_similarity as ssim

params = st.params


def display_image(img1, pfp_link):
    img1_cv = np.array(img1)
    img1_cv = cv2.cvtColor(img1_cv, cv2.COLOR_BGR2RGB)
    img1_cv = cv2.resize(img1_cv, (500, 500))
    cv2.imshow(f"PFP Image {pfp_link}", img1_cv)
    cv2.waitKey(1)


def check_pfp(pfp, y00t, folder_path, filename):
    matched_ids, missing_ids, missing_pfps = [], [], []
    twinsies, likely_pfps, likely_matches = [], [], []

    pfp_table_name = params.pfp_table_name
    engine = pg.start_db(params.db_name)

    sims, lowest_sim, highest_sim, average_sim = [], 100, 0, 0
    print("Displaying image...")
    # display_image(pfp, pfp_link)

    sim = ssim(np.array(pfp), y00t, multichannel=True)
    print("SSIM: ", sim)
    sims.append(sim)
    average_sim = sum(sims)/len(sims)
    lowest_sim = min(sims)
    highest_sim = max(sims)
    print("\nLowest SSIM: ", lowest_sim)
    print("\nHighest SSIM: ", highest_sim)
    print("\nAverage SSIM: ", average_sim, "\n")
    if sim > 0.925:
        print("\nMatched: ", pfp, filename)
        if folder_path+"/"+filename not in matched_ids:
            matched_ids.append(
                folder_path+"/"+filename)
            cv2.destroyAllWindows()
        return True, matched_ids
    if sim > 0.9:
        print("\nTwinsies: ", pfp, filename)
        if folder_path+"/"+filename not in twinsies:
            twinsies.append(folder_path+"/"+filename)
            cv2.destroyAllWindows()
        return True, twinsies
    if sim > 0.5:
        print("\nLikely Match: ", pfp, filename)
        if folder_path+"/"+filename not in likely_matches:
            likely_pfps.append(pfp)
            likely_matches.append(
                folder_path+"/"+filename)
            cv2.destroyAllWindows()
        return True, likely_pfps
    if sim < 0.4 and folder_path+"/"+filename not in missing_ids:
        missing_ids.append(folder_path+"/"+filename)
        cv2.destroyAllWindows()
        return False, "No match found"
    else:
        return False, "No match found"


# def download_degods_pfp():
    # for i in range(0, 10000):
    #     pfp_link = f"https://img-cdn.magiceden.dev/rs:fit:640:640:0:0/plain/https://metadata.degods.com/g/{i}-dead.png"
    #     try:
    #         pfp = Image.open(requests.get(pfp_link, stream=True).raw)
    #         print(f"Saving image... {i}")
    #         pfp.save(f"../outputs/degods_imgs/degod_{i}.png")
    #     except:
    #         print(f"Image {i} not found...")


# def main():
#     download_degods_pfp()


# if __name__ == "__main__":
#     main()
