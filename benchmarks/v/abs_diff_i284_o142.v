module abs_diff_i284_o142(a,b,r);
input [141:0] a,b;
output [141:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
