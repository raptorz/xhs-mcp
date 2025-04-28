from typing import Any, List, Dict, Optional
import asyncio
import json
import os
from datetime import datetime
from mcp.server.fastmcp import FastMCP,Context

import requests
from api.xhs_api import XhsApi
import logging
from urllib.parse import urlparse, parse_qs

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

mcp = FastMCP("小红书")


xhs_cookie=os.getenv('XHS_COOKIE')



def get_nodeid_token(url=None,note_id=None, xsec_token=None):
    if note_id is not None and xsec_token is not None:
        return {"note_id":note_id, "xsec_token":xsec_token}
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    note_id = parsed_url.path.split('/')[-1]
    xsec_token=None
    xsec_token_list = query_params.get('xsec_token', [None])
    if len(xsec_token_list)>0:
        xsec_token=xsec_token_list[0]
    return  {"note_id":note_id, "xsec_token":xsec_token}
@mcp.tool()
async def search_notes(keywords: str) -> str:
    """根据关键词搜索笔记

        Args:
            keywords: 搜索关键词
    """
    xhs_api = XhsApi(cookie=xhs_cookie)
    data= await xhs_api.search_notes(keywords)
    logger.info(f'keywords:{keywords},data:{data}')
    result = "搜索结果：\n\n"
    if 'data' in data and 'items' in data['data'] and len(data['data']['items'])>0:
        for i in range(0,len(data['data']['items'])):
            item = data['data']['items'][i]
            if 'note_card' in item and 'display_title' in item['note_card']:
                title=item['note_card']['display_title']
                liked_count=item['note_card']['interact_info']['liked_count']
                # cover=item['note_card']['cover']['url_default']
                url=f'https://www.xiaohongshu.com/explore/{item["id"]}?xsec_token={item["xsec_token"]}'
                result += f"{i}. {title}  \n 点赞数:{liked_count} \n   链接: {url} \n\n"
    else:
        result=f"未找到与\"{keywords}\"相关的笔记"
    return result


@mcp.tool()
async def get_note_content(url=None) -> str:
    """获取笔记内容

    Args:
        url: 笔记 URL
    """
    xhs_api = XhsApi(cookie=xhs_cookie)
    params=get_nodeid_token(url)
    data = await xhs_api.get_note_content(**params)
    logger.info(f'url:{url},params:{params},data:{data}')
    result = ""
    if 'data' in data and 'items' in data['data'] and len(data['data']['items']) > 0:
        for i in range(0, len(data['data']['items'])):
            item = data['data']['items'][i]

            if 'note_card' in item and 'user' in item['note_card']:
                note_card=item['note_card']
                cover = note_card['cover']['url_default']
                data_format=datetime.fromtimestamp(note_card.get('time',0)/1000)
                liked_count=item['note_card']['interact_info']['liked_count']
                comment_count=item['note_card']['interact_info']['comment_count']
                collected_count=item['note_card']['interact_info']['collected_count']

                url = f'https://www.xiaohongshu.com/explore/{params["note_id"]}?xsec_token={params["xsec_token"]}'
                result = f"标题: {note_card.get('title', '')}\n"
                result += f"作者: {note_card['user'].get('nickname', '')}\n"
                result += f"发布时间: {data_format}\n"
                result += f"点赞数: {liked_count}\n"
                result += f"评论数: {comment_count}\n"
                result += f"收藏数: {collected_count}\n"
                result += f"链接: {url}\n\n"
                result += f"内容:\n{note_card.get('desc', '')}"
                result += f"封面:\n{cover}"

            break
    else:
        result="获取失败"
    return result

@mcp.tool()
async def get_note_comments(url=None) -> str:
    """获取笔记评论

    Args:
        url: 笔记 URL

    """
    xhs_api = XhsApi(cookie=xhs_cookie)
    params=get_nodeid_token(url)

    data =  await xhs_api.get_note_comments(**params)
    logger.info(f'url:{url},params:{params},data:{data}')

    result=""
    if 'data' in data and 'comments' in data['data'] and len(data['data']['comments'])>0:
        for i in range(0,len(data['data']['comments'])):
            item = data['data']['comments'][i]
            data_format = datetime.fromtimestamp(item['create_time'] / 1000)

            result += f"{i}. {item['user_info']['nickname']}（{data_format}）: {item['content']}\n\n"

    else:
        result='暂无评论'

    return result

@mcp.tool()
async def post_comment(comment:str,url=None) -> str:
    """发布评论到指定笔记

    Args:
        url: 笔记 URL
        comment: 要发布的评论内容
    """
    xhs_api = XhsApi(cookie=xhs_cookie)
    params=get_nodeid_token(url)
    response= await xhs_api.post_comment(params['note_id'],comment)
    if 'success' in response and response['success']==True:
        return "回复成功"
    else:
        return "回复失败"

if __name__ == "__main__":
    logger.info("mcp run")
    mcp.run()