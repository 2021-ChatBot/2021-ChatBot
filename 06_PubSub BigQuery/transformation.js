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

      else if(messages.hasOwnProperty("event")){
            var infected = {
                  "eventId" : messages.event.eventId,
                  "companyName" : messages.event.companyName,
                  "strength" : messages.event.strength,
                  "eventTimestamp" : messages.event.infectedTime,
                  "infectedFootprintId" : messages.event.id,
                  "infectedSiteId" : messages.event.siteId,
                  "infectedMemberId" : messages.event.memberId
            }
            return JSON.stringify(infected);
      }
    }