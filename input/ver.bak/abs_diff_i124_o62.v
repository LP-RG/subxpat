module abs_diff_i124_o62(a,b,r);
input [61:0] a,b;
output [61:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
