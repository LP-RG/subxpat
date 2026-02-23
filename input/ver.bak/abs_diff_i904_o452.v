module abs_diff_i904_o452(a,b,r);
input [451:0] a,b;
output [451:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
