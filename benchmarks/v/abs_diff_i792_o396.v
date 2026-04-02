module abs_diff_i792_o396(a,b,r);
input [395:0] a,b;
output [395:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
