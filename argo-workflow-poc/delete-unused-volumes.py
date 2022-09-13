import boto3
import logging
import sys

# Enable the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt='%Y-%m-%d %H:%M:%S %Z')
ch.setFormatter(formatter)
logger.addHandler(ch)


class cleanUnusedVolumes:
    def __init__(self):
        self.DEFAULT_REGION = "us-east-1"
        self.VOLUME_COUNT = list()
        self.REGION_COUNT = list()

    # Connect to AWS boto3 Client
    def aws_connect_client(self,service,REGION):
        try:
            # Gaining API session
            #session = boto3.Session(aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
            session = boto3.Session()
            # Connect the resource
            conn_client = session.client(service, REGION)
        except Exception as e:
            logger.error(f'Could not connect to region: {REGION} and resources: {service} , Exception: {e}\n')
            conn_client = None
        return conn_client

    def get_aws_regions(self):
        try:
            get_regions = boto3.client('ec2', region_name=self.DEFAULT_REGION)
            ec2_regions = [region['RegionName'] for region in get_regions.describe_regions()['Regions']]
        except Exception as err:
            logger.error(f"Unable to get all the regions. Error : {err}")
            sys.exit(1)
        return ec2_regions

    def deleteUnusedVolume(self):

        # loop over all regions
        for region in self.get_aws_regions():
            client = boto3.client('ec2', region_name=region)
            volume_detail = client.describe_volumes()
            # process each volume in volume_detail
            if volume_detail['ResponseMetadata']['HTTPStatusCode'] == 200:
                for each_volume in volume_detail['Volumes']:
                    volName = None
                    # the volumes which do not have 'Attachments' key and their state is 'available' is considered to be unused
                    if len(each_volume['Attachments']) == 0 and each_volume['State'] == 'available':
                        self.VOLUME_COUNT.append(each_volume['VolumeId'])
                        self.REGION_COUNT.append(region)
                        try:
                            if "Tags" not in each_volume:
                                volName = None
                            elif each_volume["Tags"] is None:
                                volName = None
                            else:
                                for tag in each_volume["Tags"]:
                                    if tag['Key'] == 'Name':
                                        volName = tag['Value']
                        except KeyError as err:
                            logger.error(
                                f"Unable to get volume Tags,  error is: {err}")
                            sys.exit(1)

                        try:
                            logger.info(f"Deleting Volume with volume_id: {each_volume['VolumeId']}")
                            volume_resp = client.delete_volume(
                                VolumeId=each_volume['VolumeId']
                            )
                            if volume_resp['ResponseMetadata']['HTTPStatusCode'] == 200:
                                logger.info(f"The volume has been deleted successfully. Volume ID: {each_volume['VolumeId']}, Volume Name : {volName}, Region : {region}")
                        except Exception as err:
                            logger.error(f"Issue in deleting volume with id: {each_volume['VolumeId']} and error is: {err}")
                            sys.exit(1)
        print(f"Found {len(self.VOLUME_COUNT)} unused volumes on {len(set(self.REGION_COUNT))} region")

if __name__ == '__main__':
    callFunc = cleanUnusedVolumes()
    callFunc.deleteUnusedVolume()

