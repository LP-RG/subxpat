module abs_diff_i216_o108(a,b,r);
input [107:0] a,b;
output [107:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
