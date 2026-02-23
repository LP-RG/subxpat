module abs_diff_i168_o84(a,b,r);
input [83:0] a,b;
output [83:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
