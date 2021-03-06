from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy.sql.functions import current_user
from starlette.status import HTTP_401_UNAUTHORIZED
from .. import models, Schemas
from ..Database import get_db
from .. import oAuth2

#from random import randrange

#------------------------------Routing Parameter---------------------------

router = APIRouter(
    prefix="/partners", tags=['PARTNERS']
)

#-------------------------------------- demo array CRUD---------------------------------------

# partnerArray=[{"partnerName":"Amazon", "partnerfunction":"sell", "rating":1, "id":1},
#                 {"partnerName":"Flipkart","partnerfunction":"sell", "rating":2, "id":2},
#                 {"partnerName":"Ajio", "partnerfunction":"sell", "rating":3, "id":3}]

# def getAllValuefromId(id):
#     for i in partnerArray:
#         if i['id'] == id:
#             return i

# def findIndexFromId(id: int):
#     for i ,p in enumerate(partnerArray):
#         if p['id']==id:
#             return i


#@router.get("/", response_model=List[Schemas.PartnerResponseSchema])
@router.get("/") # Because of Join the response model for partner Schema wont work So removed it.
def getAllPartnerDetails(db: Session = Depends(get_db), current_user: Schemas.user = Depends(oAuth2.get_current_user),
                         limit: int = 10, skip: int = 0, search: Optional[str] = ""):
    #------example with SQL Alchemy--------
    #partnersList=db.query(models.Partners).filter(models.Partners.owner_id == current_user.id).all()
    partnersList = db.query(models.Partners).filter(
        models.Partners.partnername.contains(search)).limit(limit).offset(skip).all()
    #return partnersList

    #By default SQL Alchemy will use inner Join. So to make it outer Join set isouter=True:
    from sqlalchemy import func
    result = db.query(models.Partners, func.count(models.Vote.partner_id).label("Vote_count")).join(
            models.Vote, models.Vote.partner_id == models.Partners.id, isouter=True).group_by(models.Partners.id).filter(
            models.Partners.partnername.contains(search)).limit(limit).offset(skip).all()
    return result

    #print(result)
    """--> SELECT partner.id AS partner_id, partner.partnername AS partner_partnername, partner.partnerfunction AS partner_partnerfunction, partner.rating AS partner_rating, partner.published AS partner_published, partner.createdtime AS partner_createdtime, partner.owner_id AS partner_owner_id, count(votes.partner_id) AS "Vote_counte"
                            FROM partner LEFT OUTER JOIN votes ON votes.partner_id = partner.id GROUP BY partner.id"""

#------example without SQL Alchemy--------
    # cur.execute("SELECT * FROM public.partner;")
    # result=cur.fetchall()
    # print(result)
    # return result

#------example with Array--------
    #print(partnerArray)
    #return partnerArray


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Schemas.PartnerResponseSchema)
def postPartnerDetails(inputpartnerdetails: Schemas.partnerArrayModel, db: Session = Depends(get_db),
                       Current_user: Schemas.user = Depends(oAuth2.get_current_user)):

    print("User's mail id is: ", Current_user.email)

    #newPartner = models.Partners(partnername=inputpartnerdetails.partnerName ,rating=inputpartnerdetails.rating, partnerfunction=inputpartnerdetails.partnerfunction)
    newPartner = models.Partners(
        owner_id=Current_user.id, **inputpartnerdetails.dict())
    db.add(newPartner)
    db.commit()
    db.refresh(newPartner)  # its same as "RETURNING *"
    return newPartner

#------------------------------fetching from array-------------------------------
    #Converting the partnerArrayModel pydantic model will be converted into python dictionary
    #p_dict=inputpartnerdetails.dict()
    #p_dict["id"] = randrange(0,100000) # in real time it will be generated by DB
    #partnerArray.append(p_dict)
    #print(partnerArray)
    #return p_dict

#------------------------------fetching from DB without SQL Alchemy-------------------------------

    # cur.execute("insert into partner(\"partnerName\", partnerfunction, rating) values (%s, %s, %s) returning *;",
    # (inputpartnerdetails.partnerName, inputpartnerdetails.partnerfunction, inputpartnerdetails.rating))
    # result=cur.fetchone()
    # conn.commit()
    # print(result)
    # return {"message":result}


@router.get("/{partner_id}", response_model=Schemas.PartnerResponseSchema)
def getPartnerwithId(partner_id: int, db: Session = Depends(get_db),
                     Current_user: Schemas.user = Depends(oAuth2.get_current_user)):
    #def getPartnerwithId(partner_id:int, responseVal: Response):
    #------------------------------fetching from DB with SQL Alchemy-------------------------------
    filteredPartner = db.query(models.Partners).filter(
        models.Partners.id == partner_id).first()
    """We haven't used all() instead we used first() because in all() even if it get the result it will again search in the whole table
    which is waste of memory so we used first()"""
    if not filteredPartner:
        raise HTTPException(status.HTTP_404_NOT_FOUND,
                            detail=f"I found nothing for partner id: {partner_id}")

    if filteredPartner.owner_id != Current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorised to perfor this request")

    return filteredPartner

#------------------------------fetching from DB without SQL Alchemy-------------------------------
    # cur.execute("""select * from partner where id= %s""", (str(partner_id),)) #Not sure why , is rerquired
    # result=cur.fetchone()
    # if not result:
    #     raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"I found nothing for partner id: {partner_id}")

    # print(result)
    # return {"message":result}

#------------------------------fetching from array-------------------------------
#    result = getAllValuefromId(partner_id)
#    if not result:
#        #responseVal.status_code = status.HTTP_404_NOT_FOUND
#        #return {"Message": responseVal.status_code}
#        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="I found nothing.")
#    else:
#        print(partner_id," is having type: ",type(partner_id))
#        print(result)
#    return result


@router.delete("/{partner_id}", status_code=status.HTTP_204_NO_CONTENT,)
def deletePartner(partner_id: int, db: Session = Depends(get_db),
                  Current_user: Schemas.user = Depends(oAuth2.get_current_user)):
    #------------------------------deleting in DB with SQL Alchemy-------------------------------
    partner_query = db.query(models.Partners).filter(
        models.Partners.id == partner_id)
    partner_result = partner_query.first()

    if partner_result == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"id {partner_id} not found")

    if partner_result.owner_id != Current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorised to perfor this request")

    partner_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

#------------------------------deleting in DB without SQL Alchemy-------------------------------
    # cur.execute("""delete from partner where id=%s returning *""",(str(partner_id),))
    # result=cur.fetchone()
    # conn.commit()

    # if result == None:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"id {partner_id} not found")
    # print(result)
    # return Response(status_code=status.HTTP_204_NO_CONTENT)

#------------------------------deleting in array-------------------------------
    # indexVal = findIndexFromId(partner_id)
    # if indexVal == None:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"post with id: {partner_id} does not exist")

    # print("before deleting: ", partnerArray)
    # partnerArray.pop(indexVal)
    # print("after deleting: ", partnerArray)

    # return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{partner_id}", response_model=Schemas.PartnerResponseSchema)
def updateIndexInpartnerArrayModel(partner_id: int, partnerDetails: Schemas.partnerArrayModel, db: Session = Depends(get_db),
                                   Current_user: Schemas.user = Depends(oAuth2.get_current_user)):
    #------------------------------deleting in DB with SQL Alchemy-------------------------------
    partner_query = db.query(models.Partners).filter(
        models.Partners.id == partner_id)
    partner_result = partner_query.first()
    if partner_result == None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"post with id: {partner_id} does not exist")

    if partner_result.owner_id != Current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorised to perfor this request")

    partner_query.update(partnerDetails.dict(), synchronize_session=False)
    db.commit()
    db.refresh(partner_query.first())  # its same as "RETURNING *"
    return partner_query.first()

#------------------------------updating in DB without SQL Alchemy-------------------------------
    # cur.execute("""update partner set \"partnerName\"=%s, partnerfunction=%s, rating=%s where id=%s returning *;""",
    # (partnerDetails.partnerName, partnerDetails.partnerfunction, partnerDetails.rating, str(partner_id),))

    # result=cur.fetchone()

    # conn.commit()
    # if result == None:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"post with id: {partner_id} does not exist")

    # print("updated values are: ",result)
    # return result

#------------------------------updating array-------------------------------
    # indexVal = findIndexFromId(partner_id)
    # if indexVal == None:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"post with id: {partner_id} does not exist")

    # partnerDetails_dict= partnerDetails.dict()
    # partnerDetails_dict['indexVal']=indexVal
    # print("before executing put method: ",partnerArray)
    # partnerArray[indexVal]=partnerDetails_dict
    # print("After executing put method: ",partnerArray)

    # return {"data":partnerDetails_dict}
