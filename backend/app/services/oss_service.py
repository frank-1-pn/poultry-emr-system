import logging
import time

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


def _sts_configured() -> bool:
    """检查阿里云 STS 是否已配置"""
    return bool(
        settings.ALIYUN_OSS_ACCESS_KEY_ID
        and settings.ALIYUN_OSS_ACCESS_KEY_SECRET
        and settings.ALIYUN_OSS_STS_ROLE_ARN
    )


async def generate_sts_token() -> dict:
    """Generate Aliyun STS temporary credentials for direct upload.

    Uses aliyunsdksts AssumeRole when configured,
    otherwise returns stub response for development.
    """
    if not _sts_configured():
        logger.warning("阿里云 OSS STS 未配置，返回 stub 凭证")
        return {
            "access_key_id": "STS.placeholder",
            "access_key_secret": "placeholder",
            "security_token": "placeholder",
            "expiration": str(int(time.time()) + 3600),
            "bucket": settings.ALIYUN_OSS_BUCKET,
            "endpoint": settings.ALIYUN_OSS_ENDPOINT,
        }

    try:
        from aliyunsdkcore.client import AcsClient
        from aliyunsdkcore.request import CommonRequest

        client = AcsClient(
            settings.ALIYUN_OSS_ACCESS_KEY_ID,
            settings.ALIYUN_OSS_ACCESS_KEY_SECRET,
            "cn-hangzhou",
        )

        request = CommonRequest()
        request.set_accept_format("json")
        request.set_domain("sts.aliyuncs.com")
        request.set_method("POST")
        request.set_protocol_type("https")
        request.set_version("2015-04-01")
        request.set_action_name("AssumeRole")
        request.add_query_param("RoleArn", settings.ALIYUN_OSS_STS_ROLE_ARN)
        request.add_query_param("RoleSessionName", "poultry-emr-upload")
        request.add_query_param("DurationSeconds", "3600")

        response = client.do_action_with_exception(request)

        import json
        result = json.loads(response)
        credentials = result["Credentials"]

        return {
            "access_key_id": credentials["AccessKeyId"],
            "access_key_secret": credentials["AccessKeySecret"],
            "security_token": credentials["SecurityToken"],
            "expiration": credentials["Expiration"],
            "bucket": settings.ALIYUN_OSS_BUCKET,
            "endpoint": settings.ALIYUN_OSS_ENDPOINT,
        }
    except Exception as e:
        logger.error("STS AssumeRole 调用失败: %s", e)
        raise


async def generate_signed_url(oss_key: str, expires: int = 3600) -> str:
    """Generate a signed URL for private object access.

    Uses oss2 when configured, otherwise returns placeholder URL.
    """
    if not _sts_configured():
        domain = settings.ALIYUN_OSS_DOMAIN or f"https://{settings.ALIYUN_OSS_BUCKET}.{settings.ALIYUN_OSS_ENDPOINT}"
        return f"{domain}/{oss_key}?signed=placeholder&expires={expires}"

    try:
        bucket = _get_oss_bucket()
        url = bucket.sign_url("GET", oss_key, expires)

        # 如果配置了自定义域名，替换默认域名
        if settings.ALIYUN_OSS_DOMAIN:
            default_domain = f"https://{settings.ALIYUN_OSS_BUCKET}.{settings.ALIYUN_OSS_ENDPOINT}"
            url = url.replace(default_domain, settings.ALIYUN_OSS_DOMAIN)

        return url
    except Exception as e:
        logger.error("生成签名 URL 失败: %s", e)
        raise


def _get_oss_bucket():
    """获取 oss2.Bucket 实例"""
    import oss2
    auth = oss2.Auth(
        settings.ALIYUN_OSS_ACCESS_KEY_ID,
        settings.ALIYUN_OSS_ACCESS_KEY_SECRET,
    )
    return oss2.Bucket(
        auth,
        f"https://{settings.ALIYUN_OSS_ENDPOINT}",
        settings.ALIYUN_OSS_BUCKET,
    )


async def delete_oss_file(oss_key: str) -> bool:
    """删除 OSS 对象。未配置时跳过，返回 True 表示成功。"""
    if not _sts_configured():
        logger.warning("阿里云 OSS 未配置，跳过文件删除: %s", oss_key)
        return True

    try:
        bucket = _get_oss_bucket()
        bucket.delete_object(oss_key)
        logger.info("已删除 OSS 文件: %s", oss_key)
        return True
    except Exception as e:
        logger.error("删除 OSS 文件失败: %s - %s", oss_key, e)
        raise
