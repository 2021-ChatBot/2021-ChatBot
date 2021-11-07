function transform(inJson) {
      var messages = JSON.parse(inJson);

      if (messages.hasOwnProperty("member")){
            var member = {
                  "memberId" :  messages.member.id,
                  "companyName" : messages.member.companyName
            }
            return JSON.stringify(member);

      }else if(messages.hasOwnProperty("site")){
            var site = {
                  "siteId" : messages.site.id,
                  "companyName" : messages.site.companyName
            }
            return JSON.stringify(site);

      }else if(messages.hasOwnProperty("footprint")){
            var footprint = {
                  "footprintId" : messages.footprint.id,
                  "memberId" : messages.footprint.memberId,
                  "siteId" : messages.footprint.siteId,
                  "companyName" : messages.footprint.companyName
            }
            return JSON.stringify(footprint);

      }else if(messages.hasOwnProperty("event")){
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