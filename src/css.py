def run(extensions, arguments, votes_dict, measure='U', agg='sum'):
    if not extensions: 
        return []
    
    # Group votes by agent
    agents = {}
    for (ag, arg), val in votes_dict.items():
        agents.setdefault(ag, {})[arg] = val
        
    res = []
    for ext in extensions:
        # Map extension: +1 if accepted, -1 if rejected
        vec = {a: 1 if a in ext else -1 for a in arguments}
        sc = []
        
        for v in agents.values():
            # Calculate agreement (S) and disagreement (D)
            s = sum(1 for a, val in v.items() if a in vec and val == vec[a])
            d = -sum(1 for a, val in v.items() if a in vec and val == -vec[a])
            
            # Select measure
            mesures = {'S': s, 'D': d, 'U': s + d}
            sc.append(mesures.get(measure, s + d))
        
        # Aggregate scores
        if agg == 'sum':
            score = sum(sc)
        elif agg == 'min':
            score = min(sc)
        elif agg == 'leximax':
            score = sorted(sc, reverse=True)
        elif agg == 'leximin':
            score = sorted(sc)
        else:
            score = sorted(sc)
            
        res.append((ext, score))
        
    #find best score
    mx_score = max(res, key=lambda x: x[1])[1]
    
    #return all extensions with best score
    return [e for e, s in res if s == mx_score]
