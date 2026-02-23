module abs_diff_i760_o380(a,b,r);
input [379:0] a,b;
output [379:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
