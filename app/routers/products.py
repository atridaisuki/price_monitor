from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app import models, schemas

#prefix前缀
router = APIRouter(prefix="/products", tags=["products"])


@router.post("/", response_model=schemas.ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: schemas.ProductCreate,
    session: AsyncSession = Depends(get_session)
):
    """创建商品"""
    #from_orm 将schemas.productcreate格式直接转为models.product
    db_product = models.Product.from_orm(product)


    session.add(db_product)
    await session.commit()
    await session.refresh(db_product)
    return db_product


@router.get("/", response_model=List[schemas.ProductRead])
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    session: AsyncSession = Depends(get_session)
):
    """获取商品列表"""
    #异步用execute，同步用exec
    result = await session.execute(
        select(models.Product).offset(skip).limit(limit)
    )
    products = result.scalars().all()
    return products


@router.get("/{product_id}", response_model=schemas.ProductRead)
async def get_product(
    product_id: int,
    session: AsyncSession = Depends(get_session)
):
    """获取单个商品"""
    result = await session.execute(
        select(models.Product).where(models.Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )
    return product


@router.put("/{product_id}", response_model=schemas.ProductRead)
async def update_product(
    product_id: int,
    product_update: schemas.ProductUpdate,
    session: AsyncSession = Depends(get_session)
):
    """更新商品"""
    result = await session.execute(
        select(models.Product).where(models.Product.id == product_id)
    )
    db_product = result.scalar_one_or_none()
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )

    # 只更新提供的字段
    product_data = product_update.dict(exclude_unset=True)
    for field, value in product_data.items():
        setattr(db_product, field, value)

    await session.commit()
    await session.refresh(db_product)
    return db_product


@router.delete("/{product_id}", response_model=schemas.ProductRead)
async def delete_product(
    product_id: int,
    session: AsyncSession = Depends(get_session)
):
    """删除商品"""
    result = await session.execute(
        select(models.Product).where(models.Product.id == product_id)
    )
    db_product = result.scalar_one_or_none()
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )

    await session.delete(db_product)
    await session.commit()
    return db_product


@router.get("/{product_id}/history", response_model=List[schemas.PriceHistoryRead])
async def get_price_history(
    product_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    session: AsyncSession = Depends(get_session)
):
    """获取价格历史"""
    # 先验证商品是否存在
    product_result = await session.execute(
        select(models.Product).where(models.Product.id == product_id)
    )
    product = product_result.scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )

    # 获取价格历史（按时间倒序）
    result = await session.execute(
        select(models.PriceHistory)
        .where(models.PriceHistory.product_id == product_id)
        .order_by(models.PriceHistory.check_time.desc())
        .offset(skip)
        .limit(limit)
    )
    history = result.scalars().all()
    return history
