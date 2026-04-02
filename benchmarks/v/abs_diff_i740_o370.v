module abs_diff_i740_o370(a,b,r);
input [369:0] a,b;
output [369:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
