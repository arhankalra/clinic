(function () 
{
    const deck = document.getElementById('deck');
    if(!deck) 
    {
        return;
    }

    deck.addEventListener('click', async (e) => {
    const btn = e.target.closest('button');
    if(!btn) 
    {
      return;
    }

    const card = e.target.closest('.card.swipe');
    if(!card) 
    {
      return;
    }

    if(btn.hasAttribute('data-like')) 
    {
        const nctid = card.getAttribute('data-nctid');
        
        try 
        {
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = deck.dataset.addFavUrl.replace('__NCTID__', nctid);
            document.body.appendChild(form);
            form.submit();
        } 
        catch (e) 
        {
          console.error(e);
        }
    }

    card.classList.add('hidden');
  });
})();
