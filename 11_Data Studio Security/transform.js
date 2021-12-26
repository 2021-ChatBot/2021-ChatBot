function transform(inJson) {
      var messages = JSON.parse(inJson);
      
      if (messages.hasOwnProperty("member")){
            var footprint = {
                  "companyName"  : messages.member.companyName,
                  "siteId"       : null,
                  "memberId"     : messages.member.id,
                  "footprintId"  : null
            }
            return JSON.stringify(footprint);
      }
  
      else if(messages.hasOwnProperty("site")){
            var footprint = {
                  "companyName"  : messages.site.companyName,
                  "siteId"       : messages.site.id,
                  "memberId"     : null,
                  "footprintId"  : null
            }
            return JSON.stringify(footprint);
      }
  
      else if(messages.hasOwnProperty("footprint")){
            var footprint = {
                  "companyName" : messages.footprint.companyName,
                  "siteId" : messages.footprint.siteId,
                  "memberId" : messages.footprint.memberId,
                  "footprintId" : messages.footprint.id
            }
            return JSON.stringify(footprint);
      }
      else if(messages.hasOwnProperty("infected")){
            var infected = {
                  "eventId" : messages.infected.eventId,
                  "companyName" : messages.infected.companyName,
                  "strength" : messages.infected.strength,
                  "eventTimestamp" : messages.infected.eventTimestamp,
                  "infectedFootprintId" : messages.infected.footprintId,
                  "infectedSiteId" : messages.infected.siteId,
                  "infectedMemberId" : messages.infected.memberId
            }
            return JSON.stringify(infected);
      }
      else if(messages.hasOwnProperty("permission")){
          var permission = {
                "email" : messages.permission.email,
                "companyName" : messages.permission.companyName,
                "timestamp" : messages.permission.timestamp
          }
          return JSON.stringify(permission);
      }
  }