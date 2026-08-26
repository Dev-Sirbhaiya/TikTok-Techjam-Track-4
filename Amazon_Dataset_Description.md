Introduction
[🤗 Huggingface Datasets] · [📑 Paper] · [💻 GitHub]

This is a large-scale Amazon Reviews dataset, collected in 2023 by McAuley Lab, and it includes rich features such as:

User Reviews (ratings, text, helpfulness votes, etc.);

Item Metadata (descriptions, price, raw image, etc.);

Links (user-item / bought together graphs).

What’s New?
In the Amazon Reviews’23, we provide:

Larger Dataset: We collected 571.54M reviews, 245.2% larger than the last version;

Newer Interactions: Current interactions range from May. 1996 to Sep. 2023;

Richer Metadata: More descriptive features in item metadata;

Fine-grained Timestamp: Interaction timestamp at the second or finer level;

Cleaner Processing: Cleaner item metadata than previous versions;

Standard Splitting: Standard data splits to encourage RecSys benchmarking.

Citation
@article{hou2024bridging,
  title={Bridging Language and Items for Retrieval and Recommendation},
  author={Hou, Yupeng and Li, Jiacheng and He, Zhankui and Yan, An and Chen, Xiusi and McAuley, Julian},
  journal={arXiv preprint arXiv:2403.03952},
  year={2024}
}
Basic Statistics
Note

We define the #R_Tokens as the number of tokens in user reviews and #M_Tokens as the number of tokens if treating the dictionaries of item attributes as strings. We emphasize them as important statistics in the era of LLMs.

Note

We count the number of items based on user reviews rather than item metadata files. Note that some items lack metadata.

Compared to Previous Versions
Year

#Review

#User

#Item

#R_Token

#M_Token

#Domain

Timespan

2013

34.69M

6.64M

2.44M

5.91B

–

28

Jun’96 - Mar’13

2014

82.83M

21.13M

9.86M

9.16B

4.14B

24

May’96 - Jul’14

2018

233.10M

43.53M

15.17M

15.73B

7.99B

29

May’96 - Oct’18

2023

571.54M

54.51M

48.19M

30.14B

30.78B

33

May’96 - Sep’23

Grouped by Category
See also

Check Pure ID files (”ratings only” files) and corresponding data splitting strategies in Common Data Processing section.

Category

#User

#Item

#Rating

#R_Token

#M_Token

Download

All_Beauty

632.0K

112.6K

701.5K

31.6M

74.1M

review, meta

Amazon_Fashion

2.0M

825.9K

2.5M

94.9M

510.5M

review, meta

Appliances

1.8M

94.3K

2.1M

92.8M

95.3M

review, meta

Arts_Crafts_and_Sewing

4.6M

801.3K

9.0M

350.0M

695.4M

review, meta

Automotive

8.0M

2.0M

20.0M

824.9M

1.7B

review, meta

Baby_Products

3.4M

217.7K

6.0M

323.3M

218.6M

review, meta

Beauty_and_Personal_Care

11.3M

1.0M

23.9M

1.1B

913.7M

review, meta

Books

10.3M

4.4M

29.5M

2.9B

3.7B

review, meta

CDs_and_Vinyl

1.8M

701.7K

4.8M

514.8M

287.5M

review, meta

Cell_Phones_and_Accessories

11.6M

1.3M

20.8M

935.4M

1.3B

review, meta

Clothing_Shoes_and_Jewelry

22.6M

7.2M

66.0M

2.6B

5.9B

review, meta

Digital_Music

101.0K

70.5K

130.4K

11.4M

22.3M

review, meta

Electronics

18.3M

1.6M

43.9M

2.7B

1.7B

review, meta

Gift_Cards

132.7K

1.1K

152.4K

3.6M

630.0K

review, meta

Grocery_and_Gourmet_Food

7.0M

603.2K

14.3M

579.5M

462.8M

review, meta

Handmade_Products

586.6K

164.7K

664.2K

23.3M

125.8M

review, meta

Health_and_Household

12.5M

797.4K

25.6M

1.2B

787.2M

review, meta

Health_and_Personal_Care

461.7K

60.3K

494.1K

23.9M

40.3M

review, meta

Home_and_Kitchen

23.2M

3.7M

67.4M

3.1B

3.8B

review, meta

Industrial_and_Scientific

3.4M

427.5K

5.2M

235.2M

363.1M

review, meta

Kindle_Store

5.6M

1.6M

25.6M

2.2B

1.7B

review, meta

Magazine_Subscriptions

60.1K

3.4K

71.5K

3.8M

1.3M

review, meta

Movies_and_TV

6.5M

747.8K

17.3M

1.0B

415.5M

review, meta

Musical_Instruments

1.8M

213.6K

3.0M

182.2M

200.1M

review, meta

Office_Products

7.6M

710.4K

12.8M

574.7M

682.8M

review, meta

Patio_Lawn_and_Garden

8.6M

851.7K

16.5M

781.3M

875.1M

review, meta

Pet_Supplies

7.8M

492.7K

16.8M

905.9M

511.0M

review, meta

Software

2.6M

89.2K

4.9M

179.4M

67.1M

review, meta

Sports_and_Outdoors

10.3M

1.6M

19.6M

986.2M

1.3B

review, meta

Subscription_Boxes

15.2K

641

16.2K

1.0M

447.0K

review, meta

Tools_and_Home_Improvement

12.2M

1.5M

27.0M

1.3B

1.5B

review, meta

Toys_and_Games

8.1M

890.7K

16.3M

707.9M

848.3M

review, meta

Video_Games

2.8M

137.2K

4.6M

347.9M

137.3M

review, meta

Unknown

23.1M

13.2M

63.8M

3.3B

232.8M

review, meta

Quick Start
Load User Reviews
import json

file = # e.g., "All_Beauty.jsonl", downloaded from the `review` link above
with open(file, 'r') as fp:
    for line in fp:
        print(json.loads(line.strip()))
......
{
  "sort_timestamp": 1634275259292,
  "rating": 3.0,
  "helpful_votes": 0,
  "title": "Meh",
  "text": "These were lightweight and soft but much too small for my liking. I would have preferred two of these together to make one loc. For that reason I will not be repurchasing.",
  "images": [
    {
      "small_image_url": "https://m.media-amazon.com/images/I/81FN4c0VHzL._SL256_.jpg",
      "medium_image_url": "https://m.media-amazon.com/images/I/81FN4c0VHzL._SL800_.jpg",
      "large_image_url": "https://m.media-amazon.com/images/I/81FN4c0VHzL._SL1600_.jpg",
      "attachment_type": "IMAGE"
    }
  ],
  "asin": "B088SZDGXG",
  "verified_purchase": true,
  "parent_asin": "B08BBQ29N5",
  "user_id": "AEYORY2AVPMCPDV57CE337YU5LXA"
}
......
Load Item Metadata
import json

file = # e.g., "meta_All_Beauty.jsonl", downloaded from the `meta` link above
with open(file, 'r') as fp:
    for line in fp:
        print(json.loads(line.strip()))
......
{
  "main_category": "All Beauty",
  "title": "Lurrose 100Pcs Full Cover Fake Toenails Artificial Transparent Nail Tips Nail Art for DIY",
  "average_rating": 3.7,
  "rating_number": 35,
  "features": [
    "The false toenails are durable with perfect length. You have the option to wear them long or clip them short, easy to trim and file them to in any length and shape you like.",
    "ABS is kind of green enviromental material, and makes the nails durable, breathable, light even no pressure on your own nails.",
    "Fit well to your natural toenails. Non toxic, no smell, no harm to your health.",
    "Wonderful as gift for girlfriend, family and friends.",
    "The easiest and most efficient way to do your toenail tips for manicures or nail art designs. It's fashion, creative, a useful accessory brighten up your look, also as a gift."
  ],
  "description": [
    "Description",
    "The false toenails are durable with perfect length. You have the option to wear them long or clip them short, easy to trim and file them to in any length and shape you like. Plus, ABS is kind of green enviromental material, and makes the nails durable, breathable, light even no pressure on your own toenails. Fit well to your natural toenails. Non toxic, no smell, no harm to your health.",
    "Feature",
    "- Color: As Shown.- Material: ABS.- Size: 14.3 x 7.2 x 1cm.",
    "Package Including",
    "100 x Pieces fake toenails"
  ],
  "price": 6.99,
  "images": [
    {
      "hi_res": "https://m.media-amazon.com/images/I/41a1Sj7Q20L._SL1005_.jpg",
      "thumb": "https://m.media-amazon.com/images/I/31dlCd7tHSL._SS40_.jpg",
      "large": "https://m.media-amazon.com/images/I/31dlCd7tHSL.jpg",
      "variant": "MAIN"
    },
    {
      "hi_res": "https://m.media-amazon.com/images/I/510BWq7O95L._SL1005_.jpg",
      "thumb": "https://m.media-amazon.com/images/I/31sLajrdHOL._SS40_.jpg",
      "large": "https://m.media-amazon.com/images/I/31sLajrdHOL.jpg",
      "variant": "PT01"
    },
    ......
  ],
  "videos": [],
  "bought_together": null,
  "store": "Lurrose",
  "categories": [],
  "details": {
    "Color": "As Shown",
    "Size": "Large",
    "Material": "Acrylonitrile Butadiene Styrene (ABS)",
    "Brand": "Lurrose",
    "Style": "French",
    "Product Dimensions": "5.63 x 2.83 x 0.39 inches; 1.9 Ounces",
    "UPC": "799768026253",
    "Manufacturer": "Lurrose"
  },
  "parent_asin": "B07G9GWFSM"
}
......
See also

Check data loading examples and Huggingface datasets APIs in Common Data Loading section.

Data Fields
For User Reviews
Field

Type

Explanation

rating

float

Rating of the product (from 1.0 to 5.0).

title

str

Title of the user review.

text

str

Text body of the user review.

images

list

Images that users post after they have received the product. Each image has different sizes (small, medium, large), represented by the small_image_url, medium_image_url, and large_image_url respectively.

asin

str

ID of the product.

parent_asin

str

Parent ID of the product. Note: Products with different colors, styles, sizes usually belong to the same parent ID. The “asin” in previous Amazon datasets is actually parent ID. Please use parent ID to find product meta.

user_id

str

ID of the reviewer

timestamp

int

Time of the review (unix time)

verified_purchase

bool

User purchase verification

helpful_vote

int

Helpful votes of the review

For Item Metadata
Field

Type

Explanation

main_category

str

Main category (i.e., domain) of the product.

title

str

Name of the product.

average_rating

float

Rating of the product shown on the product page.

rating_number

int

Number of ratings in the product.

features

list

Bullet-point format features of the product.

description

list

Description of the product.

price

float

Price in US dollars (at time of crawling).

images

list

Images of the product. Each image has different sizes (thumb, large, hi_res). The “variant” field shows the position of image.

videos

list

Videos of the product including title and url.

store

str

Store name of the product.

categories

list

Hierarchical categories of the product.

details

dict

Product details, including materials, brand, sizes, etc.

parent_asin

str

Parent ID of the product.

bought_together

list

Recommended bundles from the websites.

Contact Us
Report Bugs: To report bugs in the dataset, please file an issue on our GitHub.

Others: For research collaborations or other questions, please email yphou AT ucsd.edu.