module abs_diff_i15360_o7680(a,b,r);
input [7679:0] a,b;
output [7679:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
