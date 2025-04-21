import boto3
import io
from PIL import Image, ImageOps
import botocore.exceptions
from configs import configs


class S3Client:
    def __init__(self,):
        self.bucket_name = configs.S3_BUCKET_NAME
        self.aws_access_key = configs.AWS_ACCESS_KEY
        self.aws_secret_key = configs.AWS_SECRET_KEY
        self.region_name = configs.REGION_NAME
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
            region_name=self.region_name
        )

    def upload_image(self, image: Image.Image, file_name: str, s3_key_folder: str = "test") -> bool:
        """
        Upload a PIL image to S3 with user_id and 'output' folder.
        :param image: PIL image to upload.
        :param file_name: Name of the image file.
        :param user_id: User ID (default: 'test').
        :return: True if upload successful, False otherwise.
        """
        try:
            # Convert PIL image to binary stream
            img_byte_array = io.BytesIO()
            image.save(img_byte_array, format="PNG")
            img_byte_array.seek(0)

            # create path S3: user_id/output/file_name.jpg
            s3_key = f"{s3_key_folder}/{file_name}"

            # Upload to S3
            self.s3.upload_fileobj(img_byte_array, self.bucket_name, s3_key, ExtraArgs={"ContentType": "image/png"})
            
            # Check file exists
            if self.check_file_exists(s3_key):
                # self.s3.generate_presigned_url(
                #     "put_object",
                #     Params={"Bucket": self.bucket_name, "Key": s3_key},
                #     ExpiresIn=3600 
                # )
                print(f"✅ Upload successful: s3://{self.bucket_name}/{s3_key}")
                return True, s3_key
            else:
                print(f"❌ Upload failed: File not found on S3")
                return False, None

        except botocore.exceptions.BotoCoreError as e:
            print(f"❌ Upload failed: {e}")
            return False

    def check_file_exists(self, s3_key: str) -> bool:
        """
        Check if a file exists in S3.
        :param s3_key: File path in S3.
        :return: True if exists, False otherwise.
        """
        try:
            self.s3.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            else:
                raise  # another 404

    def download_image(self, s3_key: str) -> Image.Image:
        try:
            if not self.check_file_exists(s3_key):
                print(f"❌ File not found on S3: s3://{self.bucket_name}/{s3_key}")
                return None

            img_byte_array = io.BytesIO()
            self.s3.download_fileobj(self.bucket_name, s3_key, img_byte_array)
            img_byte_array.seek(0) 

            image = Image.open(img_byte_array)
            image = ImageOps.exif_transpose(image)  # 🔥 Tự động điều chỉnh xoay ảnh theo EXIF
            image = image.convert("RGB")

            print(f"✅ Image downloaded from s3://{self.bucket_name}/{s3_key}")
            return image

        except botocore.exceptions.BotoCoreError as e:
            print(f"❌ Download failed: {e}")
            return None
        
    def get_region_name(self,):
        response = self.s3.get_bucket_location(Bucket=self.bucket_name)
        region_name = response.get("LocationConstraint")
        return region_name

