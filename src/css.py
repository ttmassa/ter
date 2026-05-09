from OBAF import OBAF

def run(extensions, obaf: OBAF, measure: str = 'U', agg: str = 'sum'):
    if not extensions: 
        return []
            
    res = []
    for ext in extensions:
        # Map extension: +1 if accepted, -1 if rejected
        vec = {a: 1 if a in ext else -1 for a in obaf.args}
        sc = []
        
        for v in obaf.votes.values():
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

if __name__ == "__main__":
    # Example usage
    from parser import read_apx
    from pygarg.dung import solver
    obaf = read_apx("data/test/as_01.apx")  
    extensions = solver.extension_enumeration(obaf.args, obaf.atts, "PR")
    best_extensions = run(extensions, obaf, measure='U', agg='sum')
    print("Best extensions:", best_extensions)
