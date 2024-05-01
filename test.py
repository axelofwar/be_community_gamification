# from utils import nft_inspect_tools as nft
import pandas as pd
import os
import requests
# import json
import cv2
from PIL import Image
import numpy as np
from io import BytesIO
from utils import stream_tools as st
from utils import postgres_tools as pg
from skimage.metrics import structural_similarity as ssim
import logging

params = st.params

logging.basicConfig(level=logging.DEBUG)

def display_image(img1, pfp_link):
    img1_cv = np.array(img1)
    img1_cv = cv2.cvtColor(img1_cv, cv2.COLOR_BGR2RGB)
    img1_cv = cv2.resize(img1_cv, (500, 500))
    cv2.imshow(f"Image {pfp_link}", img1_cv)
    cv2.waitKey(1)


def test_function():
    matched_ids, twinsies, missing_ids, missing_pfps = [], [], [], []

    pfp_table_name = params.pfp_table_name
    engine = pg.start_db(params.db_name)
    pfp_table = pd.read_sql_table(pfp_table_name, engine)
    pfp_links = pfp_table["PFP_Url"].values
    data = []

    for pfp_link in pfp_links:
        logging.debug(f"PFP Link: {pfp_link} - displaying image...")
        sims, lowest_sim, highest_sim, average_sim = [], 100, 0, 0
        response1 = requests.get(pfp_link)
        img1 = Image.open(BytesIO(response1.content)).convert("L")
        display_image(img1, pfp_link)
        folder_path = "outputs/y00ts_imgs"
        for filename in os.listdir(folder_path):
            if filename.endswith(".png") or filename.endswith(".jpg"):
                with open(os.path.join(folder_path, filename), "rb") as f:
                    img2_data = f.read()
                    img2 = np.array(Image.open(BytesIO(img2_data)).convert(
                        "L").resize((img1.width, img1.height)))

                    sim = ssim(np.array(img1), img2, multichannel=True)
                    logging.debug(f"SSIM: {sim}")
                    sims.append(sim)
                    average_sim = sum(sims)/len(sims)
                    lowest_sim = min(sims)
                    highest_sim = max(sims)
                    logging.debug(f"\nLowest SSIM: {lowest_sim}")
                    logging.debug(f"\nHighest SSIM: {highest_sim}")
                    logging.debug(f"\nAverage SSIM: {average_sim}\n")
                    if sim > 0.925:
                        logging.debug(f"\nMatched: {pfp_link} with {filename}")
                        if folder_path+"/"+filename not in matched_ids:
                            matched_ids.append(folder_path+"/"+filename)
                            cv2.destroyAllWindows()
                        break
                    if sim > 0.9:
                        logging.debug(f"\nTwinsies: {pfp_link} with {filename}")
                        if folder_path+"/"+filename not in twinsies:
                            twinsies.append(folder_path+"/"+filename)
                            cv2.destroyAllWindows()
                        break
                    if sim < 0.4 and folder_path+"/"+filename not in missing_ids:
                        missing_ids.append(folder_path+"/"+filename)
                        missing_pfps.append(pfp_link)

        data.append({
            "Matched IDs": matched_ids,
            "Twinsies": twinsies,
            "Missing IDs": missing_ids,
            "Lowest SSIM": lowest_sim,
            "Highest SSIM": highest_sim,
            "Average SSIM": average_sim,
            "PFP Link": pfp_link,
        })

        df = pd.DataFrame(data)
        logging.debug(f"Data Frame: {df}")

        # Save DataFrame to a JSON file
        df.to_json("outputs/matches.json")

        # Save DataFrame to a CSV file
        df.to_csv("outputs/matches.csv")

        # Save DataFrame to a Excel file
        df.to_excel("outputs/matches.xlsx")

        # Save DataFrame to a txt file
        df.to_csv("outputs/matches.txt", sep="\t", index=False)

        if cv2.namedWindow("Image", cv2.WINDOW_NORMAL):
            cv2.resizeWindow("Image", 500, 500)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

if 'GITHUB_ACTION' in os.environ:
    test_function()
    # reset logging level
    logging.basicConfig(level=logging.INFO)

test_function()
# reset logging level
logging.basicConfig(level=logging.INFO)